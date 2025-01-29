#!/usr/bin/env python3

import logging
from database import init_db, reset_db
import argparse

def main():
    parser = argparse.ArgumentParser(description='Initialize or reset the database')
    parser.add_argument('--reset', action='store_true', help='Reset the database')
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if args.reset:
        reset_db()
    else:
        init_db()

if __name__ == "__main__":
    main() 