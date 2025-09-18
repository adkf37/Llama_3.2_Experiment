#!/usr/bin/env python3
"""
Chicago Homicide Data API Fetcher

Fetches homicide data from Chicago's open data API with pagination support.
Handles large datasets by automatically managing API limits and offsets.
"""

import requests
import pandas as pd
import time
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime, timedelta
import os

class ChicagoHomicideDataFetcher:
    """Fetches and caches Chicago homicide data from the city's open data API."""
    
    def __init__(self, cache_dir: str = "./data/cache"):
        self.base_url = "https://data.cityofchicago.org/api/v3/views/iyvd-p5ga/query.csv"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API limits and pagination settings
        self.api_limit = 1000  # Default API limit
        self.max_limit = 50000  # SODA 2.0 max limit
        self.batch_size = 10000  # Optimal batch size for fetching
        
        # Cache settings
        self.cache_expiry_hours = 6  # Cache expires after 6 hours
        self.cache_file = self.cache_dir / "homicides_cache.csv"
        self.metadata_file = self.cache_dir / "cache_metadata.json"
    
    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid (not expired)."""
        if not self.cache_file.exists() or not self.metadata_file.exists():
            return False
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata.get('fetched_at', '1970-01-01'))
            expiry_time = cached_time + timedelta(hours=self.cache_expiry_hours)
            
            return datetime.now() < expiry_time
            
        except Exception as e:
            print(f"⚠️  Error checking cache validity: {e}")
            return False
    
    def get_total_record_count(self) -> int:
        """Get the total number of records available via API."""
        try:
            # Use $select=count(*) to get total count efficiently
            count_url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json?$select=count(*)"
            response = requests.get(count_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return int(data[0].get('count', 0))
            
        except Exception as e:
            print(f"⚠️  Could not get record count: {e}")
            
        # Fallback: estimate based on known data size
        return 15000  # Conservative estimate
    
    def fetch_batch(self, offset: int, limit: int) -> pd.DataFrame:
        """Fetch a batch of records from the API."""
        params = {
            '$offset': offset,
            '$limit': min(limit, self.max_limit)
        }
        
        try:
            print(f"  📥 Fetching records {offset:,} to {offset + limit:,}...")
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            
            if response.text.strip():
                # Read CSV data into DataFrame
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                print(f"  ✅ Retrieved {len(df):,} records")
                return df
            else:
                print(f"  ⚠️  Empty response for offset {offset}")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error fetching batch at offset {offset}: {e}")
            raise
        except pd.errors.EmptyDataError:
            print(f"  ⚠️  No more data available at offset {offset}")
            return pd.DataFrame()
    
    def fetch_all_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch all homicide data from the API with pagination.
        Uses caching to avoid unnecessary API calls.
        """
        if not force_refresh and self.is_cache_valid():
            print("📋 Using cached data (still fresh)")
            return self.load_from_cache()
        
        print("🌐 Fetching fresh data from Chicago Open Data API...")
        
        # Get total record count
        total_records = self.get_total_record_count()
        print(f"📊 Estimated total records: {total_records:,}")
        
        all_dataframes = []
        offset = 0
        batch_count = 0
        
        while True:
            try:
                # Fetch batch
                batch_df = self.fetch_batch(offset, self.batch_size)
                
                if batch_df.empty:
                    print("  🏁 No more records available")
                    break
                
                all_dataframes.append(batch_df)
                batch_count += 1
                
                # Update offset for next batch
                offset += len(batch_df)
                
                # If we got less than requested, we've reached the end
                if len(batch_df) < self.batch_size:
                    print("  🏁 Reached end of dataset")
                    break
                
                # Add small delay to be respectful to the API
                time.sleep(0.5)
                
                # Safety check to prevent infinite loops
                if batch_count > 100:  # Max 1M records
                    print("  ⚠️  Reached batch limit, stopping")
                    break
                
            except Exception as e:
                print(f"❌ Error during batch fetch: {e}")
                if all_dataframes:
                    print("🔄 Using partial data fetched so far...")
                    break
                else:
                    raise
        
        if not all_dataframes:
            raise ValueError("No data could be fetched from the API")
        
        # Combine all batches
        print(f"🔗 Combining {len(all_dataframes)} batches...")
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Remove duplicates (in case of overlapping batches)
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates()
        final_count = len(combined_df)
        
        if initial_count != final_count:
            print(f"🧹 Removed {initial_count - final_count:,} duplicate records")
        
        print(f"✅ Successfully fetched {final_count:,} total records")
        
        # Cache the results
        self.save_to_cache(combined_df)
        
        return combined_df
    
    def save_to_cache(self, df: pd.DataFrame) -> None:
        """Save DataFrame to cache with metadata."""
        try:
            # Save data
            df.to_csv(self.cache_file, index=False)
            
            # Save metadata
            metadata = {
                'fetched_at': datetime.now().isoformat(),
                'record_count': len(df),
                'columns': list(df.columns),
                'data_source': 'Chicago Open Data API',
                'api_url': self.base_url
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 Data cached to: {self.cache_file}")
            
        except Exception as e:
            print(f"⚠️  Could not cache data: {e}")
    
    def load_from_cache(self) -> pd.DataFrame:
        """Load data from cache."""
        try:
            df = pd.read_csv(self.cache_file)
            
            # Load metadata for info
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata.get('fetched_at', '1970-01-01'))
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            
            print(f"📋 Loaded {len(df):,} records from cache (age: {age_hours:.1f} hours)")
            return df
            
        except Exception as e:
            print(f"❌ Error loading cache: {e}")
            raise
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached data."""
        if not self.metadata_file.exists():
            return {"cached": False}
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata.get('fetched_at', '1970-01-01'))
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            
            return {
                "cached": True,
                "fetched_at": metadata.get('fetched_at'),
                "age_hours": round(age_hours, 1),
                "record_count": metadata.get('record_count', 0),
                "is_valid": self.is_cache_valid(),
                "cache_file": str(self.cache_file),
                "expires_in_hours": max(0, self.cache_expiry_hours - age_hours)
            }
            
        except Exception as e:
            return {"cached": False, "error": str(e)}
    
    def clear_cache(self) -> None:
        """Clear cached data."""
        try:
            if self.cache_file.exists():
                os.remove(self.cache_file)
                print(f"🗑️  Removed cache file: {self.cache_file}")
            
            if self.metadata_file.exists():
                os.remove(self.metadata_file)
                print(f"🗑️  Removed metadata file: {self.metadata_file}")
                
        except Exception as e:
            print(f"⚠️  Error clearing cache: {e}")

def main():
    """Test the data fetcher."""
    fetcher = ChicagoHomicideDataFetcher()
    
    # Show cache info
    cache_info = fetcher.get_cache_info()
    print(f"📋 Cache info: {cache_info}")
    
    # Fetch data
    try:
        df = fetcher.fetch_all_data()
        print(f"\n📊 Data summary:")
        print(f"  Records: {len(df):,}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"  Sample columns: {list(df.columns[:5])}")
        
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")

if __name__ == "__main__":
    main()
