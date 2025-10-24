#!/usr/bin/env python3
"""
Seed Vector Index Script for Veda Healthcare Chatbot.
Ingests healthcare documents into Pinecone vector database for RAG.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.rag.pipeline import RAGPipeline
from app.core.config import DOCUMENTS_PATH, USE_DEV_LLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_sample_documents(docs_path: str):
    """Create sample healthcare documents for testing."""
    
    docs_dir = Path(docs_path)
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    sample_docs = {
        "headache_guide.txt": """
# Headache Guide

## Types of Headaches

### Tension Headaches
Tension headaches are the most common type of headache. They feel like a tight band around your head and can be caused by:
- Stress and anxiety
- Poor posture
- Eye strain from screens
- Dehydration
- Lack of sleep
- Muscle tension in neck and shoulders

### Migraines
Migraines are severe headaches that can last for hours or days. Symptoms include:
- Throbbing pain, usually on one side
- Sensitivity to light and sound
- Nausea and vomiting
- Visual disturbances (aura)
- Triggers: certain foods, hormonal changes, stress, weather changes

### Cluster Headaches
Cluster headaches are rare but extremely painful. They:
- Occur in cycles or clusters
- Cause severe pain around one eye
- May cause eye redness and tearing
- Usually last 15 minutes to 3 hours

## When to Seek Medical Attention
- Sudden, severe headache unlike any before
- Headache with fever, stiff neck, confusion
- Headache after head injury
- Progressive worsening of headaches
- Headache with vision changes or weakness
        """,
        
        "fever_management.txt": """
# Fever Management Guide

## Understanding Fever
Fever is a temporary increase in body temperature, often due to illness. It's a sign that your body is fighting infection.

### Normal Temperature Ranges
- Normal: 97°F to 99°F (36.1°C to 37.2°C)
- Low-grade fever: 99°F to 100.3°F (37.2°C to 37.9°C)
- Fever: 100.4°F (38°C) or higher

### Common Causes
- Viral infections (flu, common cold)
- Bacterial infections
- Inflammatory conditions
- Heat exhaustion
- Certain medications
- Vaccines (temporary)

### Home Treatment
- Rest and stay hydrated
- Take fever reducers (acetaminophen, ibuprofen)
- Use cool compresses
- Wear light clothing
- Take lukewarm baths

### When to See a Doctor
Adults should seek medical care if:
- Fever is 103°F (39.4°C) or higher
- Fever lasts more than 3 days
- Severe symptoms accompany fever
- Signs of dehydration
- Difficulty breathing
- Persistent vomiting

Children and infants have different guidelines and should be evaluated more quickly.
        """,
        
        "diabetes_overview.txt": """
# Diabetes Overview

## What is Diabetes?
Diabetes is a group of metabolic disorders characterized by high blood sugar levels over a prolonged period.

### Types of Diabetes

#### Type 1 Diabetes
- Usually diagnosed in children and young adults
- Body doesn't produce insulin
- Requires daily insulin injections
- Autoimmune condition
- About 5-10% of diabetes cases

#### Type 2 Diabetes
- Most common form (90-95% of cases)
- Body doesn't use insulin properly
- Often develops in adults over 45
- Risk factors: obesity, family history, sedentary lifestyle
- May be managed with diet, exercise, and medication

#### Gestational Diabetes
- Develops during pregnancy
- Usually resolves after delivery
- Increases risk of Type 2 diabetes later

### Symptoms
- Frequent urination
- Excessive thirst
- Unexplained weight loss
- Fatigue
- Blurred vision
- Slow-healing wounds
- Frequent infections

### Complications
Long-term complications can include:
- Heart disease
- Stroke
- Kidney disease
- Eye problems
- Nerve damage
- Poor wound healing

### Management
- Regular blood sugar monitoring
- Healthy diet
- Regular exercise
- Medication as prescribed
- Regular medical checkups
        """,
        
        "hypertension_info.txt": """
# Hypertension (High Blood Pressure) Information

## Understanding Blood Pressure
Blood pressure is the force of blood against artery walls. It's measured in millimeters of mercury (mmHg) and recorded as two numbers:
- Systolic pressure (top number): pressure when heart beats
- Diastolic pressure (bottom number): pressure when heart rests

### Blood Pressure Categories
- Normal: Less than 120/80 mmHg
- Elevated: 120-129 systolic and less than 80 diastolic
- Stage 1 Hypertension: 130-139/80-89 mmHg
- Stage 2 Hypertension: 140/90 mmHg or higher
- Hypertensive Crisis: Higher than 180/120 mmHg (seek immediate care)

## Risk Factors
### Controllable Factors
- Diet high in sodium
- Lack of physical activity
- Obesity
- Smoking
- Excessive alcohol consumption
- Stress
- Sleep apnea

### Uncontrollable Factors
- Age (risk increases with age)
- Family history
- Race (higher risk in African Americans)
- Gender (men at higher risk until age 65)

## Symptoms
Hypertension is often called the "silent killer" because it usually has no symptoms until complications develop. Some people may experience:
- Headaches
- Shortness of breath
- Nosebleeds
- Dizziness

## Complications
Untreated hypertension can lead to:
- Heart attack
- Stroke
- Heart failure
- Kidney disease
- Vision problems
- Peripheral artery disease

## Management
### Lifestyle Changes
- Maintain healthy weight
- Exercise regularly (at least 30 minutes most days)
- Eat a healthy diet (DASH diet recommended)
- Limit sodium intake
- Limit alcohol consumption
- Don't smoke
- Manage stress
- Get adequate sleep

### Medications
Various types of blood pressure medications may be prescribed:
- ACE inhibitors
- ARBs (Angiotensin receptor blockers)
- Diuretics
- Beta-blockers
- Calcium channel blockers
        """,
        
        "chest_pain_guide.txt": """
# Chest Pain Guide

## Types of Chest Pain

### Cardiac Chest Pain
Signs that chest pain may be heart-related:
- Crushing or squeezing sensation
- Pain radiating to arm, jaw, or back
- Shortness of breath
- Sweating
- Nausea
- Dizziness

### Non-Cardiac Chest Pain
Other causes of chest pain include:
- Muscle strain
- Rib injury
- Acid reflux (GERD)
- Anxiety or panic attacks
- Lung problems (pneumonia, pleurisy)
- Costochondritis (inflammation of rib cartilage)

## Emergency Warning Signs
Call 911 immediately if experiencing:
- Sudden, severe chest pain
- Chest pain with shortness of breath
- Pain radiating to arm, jaw, or back
- Chest pain with sweating, nausea, or dizziness
- Feeling of impending doom

## When to See a Doctor
Seek medical attention for:
- New or worsening chest pain
- Chest pain with exertion
- Recurring chest pain
- Chest pain with fever
- Any chest pain that concerns you

## Risk Factors for Heart Disease
- High blood pressure
- High cholesterol
- Diabetes
- Smoking
- Family history of heart disease
- Obesity
- Sedentary lifestyle
- Age (men over 45, women over 55)

## Prevention
- Maintain a healthy diet
- Exercise regularly
- Don't smoke
- Limit alcohol
- Manage stress
- Control blood pressure and cholesterol
- Maintain healthy weight
- Get regular checkups
        """
    }
    
    for filename, content in sample_docs.items():
        file_path = docs_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        logger.info(f"Created sample document: {file_path}")
    
    logger.info(f"Created {len(sample_docs)} sample documents in {docs_path}")


async def seed_vector_index(docs_path: str = None, create_samples: bool = False):
    """
    Seed the vector index with healthcare documents.
    
    Args:
        docs_path: Path to documents directory
        create_samples: Whether to create sample documents
    """
    
    docs_path = docs_path or DOCUMENTS_PATH
    
    logger.info(f"Starting vector index seeding process...")
    logger.info(f"Documents path: {docs_path}")
    logger.info(f"Development mode: {USE_DEV_LLM}")
    
    # Create sample documents if requested
    if create_samples:
        logger.info("Creating sample healthcare documents...")
        await create_sample_documents(docs_path)
    
    # Check if documents directory exists
    if not os.path.exists(docs_path):
        logger.error(f"Documents directory does not exist: {docs_path}")
        if not create_samples:
            logger.info("Use --create-samples to create sample documents")
        return False
    
    try:
        # Initialize RAG pipeline
        logger.info("Initializing RAG pipeline...")
        rag = RAGPipeline()
        
        # Get pipeline stats
        stats = rag.get_stats()
        logger.info(f"RAG Pipeline Mode: {stats['mode']}")
        logger.info(f"Embedding Model: {stats['embedding_model']}")
        logger.info(f"Chunk Size: {stats['chunk_size']}")
        
        # Perform health check
        health = await rag.health_check()
        logger.info(f"RAG Pipeline Health: {health['status']}")
        
        if health['status'] != 'healthy':
            logger.warning("RAG pipeline health check failed, but continuing...")
        
        # Ingest documents
        logger.info("Starting document ingestion...")
        chunk_count = await rag.ingest_documents(docs_path)
        
        if chunk_count > 0:
            logger.info(f"✅ Successfully ingested {chunk_count} document chunks")
            
            # Test retrieval
            logger.info("Testing document retrieval...")
            test_queries = [
                "headache symptoms",
                "fever treatment",
                "diabetes management",
                "high blood pressure"
            ]
            
            for query in test_queries:
                results = await rag.retrieve(query, top_k=2)
                logger.info(f"Query '{query}' returned {len(results)} results")
                if results:
                    logger.info(f"  Top result: {results[0]['text'][:100]}...")
            
            return True
        else:
            logger.warning("No documents were ingested")
            return False
            
    except Exception as e:
        logger.error(f"Error during vector index seeding: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function with command line argument parsing."""
    
    parser = argparse.ArgumentParser(description="Seed vector index with healthcare documents")
    parser.add_argument(
        "--docs-path",
        type=str,
        default=DOCUMENTS_PATH,
        help=f"Path to documents directory (default: {DOCUMENTS_PATH})"
    )
    parser.add_argument(
        "--create-samples",
        action="store_true",
        help="Create sample healthcare documents"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🏥 Veda Healthcare Chatbot - Vector Index Seeding")
    logger.info("=" * 50)
    
    success = await seed_vector_index(
        docs_path=args.docs_path,
        create_samples=args.create_samples
    )
    
    if success:
        logger.info("✅ Vector index seeding completed successfully!")
        return 0
    else:
        logger.error("❌ Vector index seeding failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)