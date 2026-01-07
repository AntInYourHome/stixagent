"""Main entry point for STIX Agent."""
import argparse
import json
import sys
from pathlib import Path

from stixagent.loaders import DocumentLoader
from stixagent.agents import STIXAgent
from stixagent.utils.stix_converter import STIXConverter
from stixagent.utils.logger import setup_logging, get_logger
from config import DEBUG_MODE, LOG_FILE, LOG_LEVEL


def main():
    """Main function to run STIX conversion."""
    parser = argparse.ArgumentParser(
        description="Convert penetration test cases to STIX 2.1 format"
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Input file path (PDF, PPT, TXT, HTML)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path for STIX JSON (default: stdout)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output STIX JSON"
    )
    parser.add_argument(
        "--react",
        action="store_true",
        help="Use ReAct agent with text splitting for large documents"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Log file path (default: ./logs/stixagent.log)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    debug_mode = args.debug or DEBUG_MODE
    log_file = args.log_file or (LOG_FILE if not args.debug else None)
    setup_logging(debug=debug_mode, log_file=log_file)
    logger = get_logger()
    
    if debug_mode:
        logger.debug("Debug mode enabled")
    
    # Load document
    logger.info(f"Loading document: {args.input_file}")
    try:
        documents = DocumentLoader.load_document(args.input_file)
        logger.info(f"Loaded {len(documents)} document chunks")
        
        # Combine all document chunks
        full_content = "\n\n".join([doc.page_content for doc in documents])
        metadata = documents[0].metadata if documents else {}
        
    except Exception as e:
        print(f"Error loading document: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize agent
    logger.info("Initializing STIX Agent...")
    try:
        agent = STIXAgent()
        logger.info("STIX Agent initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing agent: {e}", exc_info=True)
        sys.exit(1)
    
    # Convert to STIX
    logger.info("Converting to STIX 2.1 format...")
    try:
        # Use ReAct mode if requested or document is large
        use_react = args.react or len(full_content) > 3000
        if use_react:
            logger.info("Using ReAct agent with text splitting...")
        stix_output = agent.convert_to_stix(full_content, metadata, use_react=use_react)
        logger.info("STIX conversion completed")
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate if requested
    if args.validate:
        logger.info("Validating STIX output...")
        try:
            stix_data = json.loads(stix_output)
            is_valid, error = STIXConverter.validate_stix_json(stix_data)
            if is_valid:
                logger.info("STIX output is valid")
                print("[OK] STIX output is valid")
            else:
                logger.error(f"STIX validation failed: {error}")
                print(f"[FAIL] STIX validation failed: {error}", file=sys.stderr)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            print(f"[FAIL] Invalid JSON: {e}", file=sys.stderr)
    
    # Output result
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(stix_output)
        logger.info(f"STIX output saved to: {args.output}")
        print(f"STIX output saved to: {args.output}")
    else:
        print("\n" + "="*80)
        print("STIX 2.1 Output:")
        print("="*80)
        print(stix_output)


if __name__ == "__main__":
    main()

