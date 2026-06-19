import os
import logging
import lightkurve as lk

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory configuration
RAW_DATA_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

# Recommended presets for academic demonstration
PRESETS = {
    "exoplanet": [
        {"tic_id": 307210830, "sector": 1, "name": "L 98-59 / TOI-175"},
        {"tic_id": 257605131, "sector": 4, "name": "TOI-451"}
    ],
    "eclipsing_binary": [
        {"tic_id": 260132367, "sector": 1, "name": "TOI-1338 (Circumbinary)"},
        {"tic_id": 233887812, "sector": 1, "name": "EB Candidate"}
    ],
    "starspot": [
        {"tic_id": 445493624, "sector": 1, "name": "Active Spotted Star"},
        {"tic_id": 281541554, "sector": 1, "name": "Rotational Modulator"}
    ],
    "noise": [
        {"tic_id": 25155490, "sector": 1, "name": "Quiet Control Star"}
    ]
}

def download_target_fits(tic_id, sector=None, output_dir=RAW_DATA_DIR):
    """
    Search and download a TESS light curve for a given TIC ID, saving it as a FITS file.
    """
    query_str = f"TIC {tic_id}"
    logger.info(f"Searching for TESS light curves for {query_str}...")
    
    try:
        # Search light curve products from SPOC or QLP
        search_result = lk.search_lightcurve(query_str, mission="TESS")
        
        if len(search_result) == 0:
            logger.warning(f"No TESS light curves found for TIC {tic_id}.")
            return None
        
        # Filter by sector if specified
        if sector is not None:
            sector_results = search_result[search_result.sector == sector]
            if len(sector_results) > 0:
                search_result = sector_results
            else:
                logger.warning(f"Sector {sector} not found for TIC {tic_id}. Downloading default sector.")
        
        # Download the first available SPOC or QLP light curve
        # Prefer SPOC if available as it is 2-minute cadence and has PDCSAP flux
        spoc_results = search_result[search_result.author == "SPOC"]
        if len(spoc_results) > 0:
            lc_file = spoc_results[0].download()
        else:
            lc_file = search_result[0].download()
            
        if lc_file is None:
            logger.error(f"Download failed for TIC {tic_id}.")
            return None
            
        # Define output filename
        actual_sector = lc_file.sector
        filename = f"tic_{tic_id}_sector_{actual_sector}.fits"
        filepath = os.path.join(output_dir, filename)
        
        # Write to FITS file
        lc_file.to_fits(filepath, overwrite=True)
        logger.info(f"Successfully downloaded and saved {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error downloading TIC {tic_id}: {str(e)}")
        return None

def download_all_presets():
    """
    Downloads all preset TIC targets for the research dataset.
    """
    downloaded_files = {}
    for category, targets in PRESETS.items():
        downloaded_files[category] = []
        for target in targets:
            filepath = download_target_fits(target["tic_id"], target["sector"])
            if filepath:
                downloaded_files[category].append(filepath)
    return downloaded_files

if __name__ == "__main__":
    logger.info("Initializing TESS data downloader...")
    # Download a small subset of presets for verification
    download_target_fits(307210830, sector=1) # L 98-59
