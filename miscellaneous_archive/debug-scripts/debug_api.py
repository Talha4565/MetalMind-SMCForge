import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from api.app.main import model_manager, load_asset_data, engineer_all_features
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

def deep_diagnostic():
    asset = "gold"
    print(f"\n--- Deep Diagnostic for {asset} ---")
    
    try:
        # 1. Check Model
        model, feature_names = model_manager.get_or_load_model(asset)
        if model is None:
            print(f"❌ ERROR: Model file not found.")
            return

        print(f"✅ Model Loaded. Expected features: {len(feature_names) if feature_names else 'Unknown'}")
        if feature_names:
            print(f"Sample of expected features: {feature_names[:5]}")

        # 2. Check Raw Data
        print("\n--- Loading Data ---")
        df = load_asset_data(asset=asset, primary_tf='15m', session_filter=True)
        print(f"✅ Aligned raw data shape: {df.shape}")
        
        # 3. Check Feature Engineering
        print("\n--- Engineering Features ---")
        df_feat = engineer_all_features(df, add_labels=False)
        print(f"✅ Engineered features shape: {df_feat.shape}")
        
        # 4. Check for Intersection
        if feature_names:
            current_cols = list(df_feat.columns)

            # Create a normalized mapping for current columns
            col_lookup = {}
            for col in current_cols:
                # Basic normalization: lowercase and strip underscores
                norm = col.lower().replace('_', '')
                col_lookup[norm] = col

                # Handle specific session shorthands
                if norm == 'sessionasia': col_lookup['asia'] = col
                if norm == 'sessionlondon' or norm == 'sessionldn': col_lookup['ldn'] = col
                if norm == 'sessionny': col_lookup['ny'] = col

            missing = []
            found_and_mapped = {}

            for f in feature_names:
                if f in current_cols:
                    found_and_mapped[f] = f
                else:
                    # Try normalized matching
                    feat_norm = f.lower().replace('_', '')
                    if feat_norm in col_lookup:
                        found_and_mapped[col_lookup[feat_norm]] = f
                    else:
                        missing.append(f)

            print(f"\n--- Feature Mapping Analysis ---")
            print(f"Mappable features: {len(found_and_mapped)}/{len(feature_names)}")
            if missing:
                print(f"❌ MISSING FEATURES ({len(missing)}): {missing}")
            else:
                print(f"✅ ALL FEATURES MAPPED SUCCESSFULLY")

            if len(found_and_mapped) < len(feature_names):
                print("\nCRITICAL: The current data engine is NOT producing all features this model was trained on.")
                print("We may need to retrain the model or update the feature pipeline.")
            else:
                print("\nSUCCESS: All expected model features are present in the current engineering pipeline.")        
    except Exception as e:
        print(f"💥 CRASH DURING DIAGNOSTIC: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deep_diagnostic()
