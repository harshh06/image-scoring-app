"""
prepare_ap_dataset.py
=====================
Prepares the AP histology dataset for model training by:
  1. Parsing the hardcoded scoring table into a label lookup dict.
  2. Scanning all subfolders in AP_SOURCE_DIR for .tif image files
     (skipping MetaData/ folders).
  3. Mapping each image filename → sample ID → scores.
  4. Copying ONLY labeled images to DEST_IMAGE_DIR.
  5. Writing dataset/final_labels_for_training.csv with columns:
       filename, edema, necrosis, inflammation, total
     where 'total' is RECALCULATED as edema + necrosis + inflammation.

Usage:
    python prepare_ap_dataset.py
"""

import csv
import shutil
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# PATHS  (edit if needed)
# ──────────────────────────────────────────────────────────────────────────────
AP_SOURCE_DIR  = Path("/Users/harshsoni/Downloads/ap-scoring")
PROJECT_DIR    = Path(__file__).parent
DEST_IMAGE_DIR = PROJECT_DIR / "dataset" / "processed_images"
OUTPUT_CSV     = PROJECT_DIR / "dataset" / "final_labels_for_training.csv"

# ──────────────────────────────────────────────────────────────────────────────
# SCORING DATA
# Format: "SAMPLE_ID  EDEMA  NECROSIS  INFLAMMATION"
# • Rows where any score column is non-numeric are omitted below.
# • Total is NOT taken from the source table — it is recalculated
#   as Edema + Necrosis + Inflammation.
# • S-3569 (all blank) and S-3674 ("not stained well") are excluded.
# ──────────────────────────────────────────────────────────────────────────────
RAW_SCORES = """
S-3536-01  1.5  2    2
S-3536-02  2    1    1.5
S-3536-03  2    2    2
S-3536-04  2.5  2    2
S-3536-05  2.5  3    3
S-3536-06  2.5  3    3
S-3536-07  1.5  2    2
S-3536-08  1    2    2
S-3536-09  2    2    2
S-3536-10  1.5  2    2
S-3536-11  1.5  2    2
S-3536-12  2    2    2
S-3536-13  3.5  2    3

S-3537-01  1.5  1    1
S-3537-02  1    1    1
S-3537-03  1.5  1    1
S-3537-04  2    2    1.5
S-3537-05  2.5  3    2
S-3537-06  1.5  2.5  2
S-3537-07  3.5  4    4
S-3537-08  0.5  1    0.5
S-3537-09  1.5  2    2
S-3537-10  1.5  2    2
S-3537-11  2    3    3
S-3537-12  2    2    2

S-3538-01  1.5  2    2
S-3538-02  0.5  1    0.5
S-3538-03  1    1.5  1
S-3538-04  2    2    2
S-3538-05  0.5  1    0.5
S-3538-06  1    1.5  1
S-3538-07  1    1.5  1
S-3538-08  0.5  1    0.5
S-3538-09  2    2.5  3
S-3538-10  2    2.5  3
S-3538-11  1.5  2    2
S-3538-12  2    2    2
S-3538-13  3.5  3    4
S-3538-14  2.5  3    3

S-3539-01  0.5  1    0.5
S-3539-02  1    2    2
S-3539-03  2    2    2
S-3539-04  3    4    4
S-3539-05  3    2    2
S-3539-06  2    3    3
S-3539-07  1    1.5  1
S-3539-08  1    1.5  1
S-3539-09  1    1.5  1
S-3539-10  1    2    2
S-3539-11  2    3    3
S-3539-12  2    2    2

S-3540-01  2    3    3
S-3540-02  2    2    2
S-3540-03  2.5  2    3
S-3540-04  3    3    3
S-3540-05  3    4    4
S-3540-06  3    4    3
S-3540-07  3    4    4
S-3540-08  2    4    3
S-3540-09  2    3    3
S-3540-10  2    3    2
S-3540-11  2    3    3
S-3540-12  3    3    4
S-3540-13  2    3    3

S-3541-01  0    0    0
S-3541-02  0    0    0
S-3541-03  2    2    2
S-3541-04  0.5  0.5  0.5
S-3541-05  1    3    2
S-3541-06  2    2    2
S-3541-07  1    1    1
S-3541-08  2    1    1
S-3541-09  1    1    1
S-3541-10  1    0    0
S-3541-11  0    0    0
S-3541-12  0.5  1    0.5

S-3542-01  2    2    2
S-3542-02  3    3    3
S-3542-03  3    3.5  3
S-3542-04  2.5  3    3
S-3542-05  3    4    4
S-3542-06  0.5  1    1
S-3542-07  0.5  1    1
S-3542-08  1    1    1
S-3542-09  1    1    1
S-3542-10  0.5  1    1
S-3542-11  0.5  1    1
S-3542-12  1    2    2
S-3542-13  1    2    2

S-3543-01  0    0    1
S-3543-02  0    0    0
S-3543-03  1    1    1
S-3543-04  1    1    1
S-3543-05  1    2    1
S-3543-06  1.5  1    2
S-3543-07  0    0    0
S-3543-08  0    1    1
S-3543-09  1    1    1
S-3543-10  1    1    1
S-3543-11  1    1.5  1
S-3543-12  2    2    2
S-3543-13  2.5  3    3
S-3543-14  1.5  2    2

S-3544-01  0.5  1    1
S-3544-02  0.5  1    1
S-3544-03  0    0.5  0
S-3544-04  1    1    1
S-3544-05  0.5  1    1
S-3544-06  0.5  0.5  0.5
S-3544-07  0    0    0.5
S-3544-08  0.5  0.5  0.5
S-3544-09  1    1    1
S-3544-10  1    1    2
S-3544-11  2    2    2

S-3545-01  4    4    4
S-3545-02  1    1    1
S-3545-03  1    0.5  0.5
S-3545-04  1    1    1
S-3545-05  1    1    1
S-3545-06  1    0.5  0.5
S-3545-07  0.5  0.5  0.5
S-3545-08  1    1    1
S-3545-09  1    1    1
S-3545-10  1    1    1
S-3545-11  1    1    1
S-3545-12  1    1    1
S-3545-13  1    2    1

S-3546-01  1    1    1
S-3546-02  0    0    0
S-3546-03  0.5  0    0
S-3546-04  1    1    1
S-3546-05  2    2    2
S-3546-06  2    4    3
S-3546-07  2    2    2
S-3546-08  2    2    2
S-3546-09  0    0    0
S-3546-10  0    0    0

S-3547-01  2    3    2
S-3547-02  2    2    2
S-3547-03  1    2    2
S-3547-04  1    1    1
S-3547-05  2    2    2
S-3547-06  4    4    4
S-3547-07  3    3    3
S-3547-08  2.5  3    2.5
S-3547-09  2    3    2.5
S-3547-10  2    3    2
S-3547-11  3    3    3
S-3547-12  2    2.5  3
S-3547-13  1    2    2

S-3548-01  2    2    2
S-3548-02  2    3    2
S-3548-03  2    3.5  3
S-3548-04  2    3    3
S-3548-05  1    1    1
S-3548-06  2    2.5  2.5
S-3548-07  1    2.5  2
S-3548-09  2    2    2
S-3548-10  2    3.5  3
S-3548-11  2    3    2
S-3548-12  1    2.5  2

S-3549-01  2    2    2
S-3549-02  3    4    3
S-3549-03  4    4    4
S-3549-04  0    0    0
S-3549-05  0    1    0
S-3549-06  1    1    1
S-3549-07  0    0    0
S-3549-08  0    1    1
S-3549-09  1    2    2
S-3549-10  1    1    1
S-3549-11  1    1    1
S-3549-12  1    1    1
S-3549-13  1.5  1    1

S-3550-01  3    4    3
S-3550-02  3    4    3
S-3550-03  2    2    2
S-3550-04  1    2    2
S-3550-05  2    3    3
S-3550-06  2    3    3
S-3550-07  3    4    3
S-3550-08  3    4    3
S-3550-09  4    4    4
S-3550-10  4    4    4
S-3550-11  4    4    4

S-3551-01  2    3    3
S-3551-02  3    3    3
S-3551-03  4    4    4
S-3551-04  2    2    2
S-3551-05  2    3    2
S-3551-06  2    2    2
S-3551-07  2    2    2
S-3551-08  3    3    2
S-3551-09  1    1    1
S-3551-10  2    3    3
S-3551-11  2    3    3

S-3552-01  1    1    1
S-3552-02  0.5  1    1
S-3552-03  0    0    0
S-3552-04  0    0    0
S-3552-05  1    1    1
S-3552-06  1    2    1
S-3552-07  1    0    0
S-3552-08  1    1    1
S-3552-09  0    0    0
S-3552-10  4    4    4
S-3552-11  1    2    2
S-3552-12  2.5  1.5  2

S-3553-01  3    4    4
S-3553-02  2    3    3
S-3553-03  2    3    3
S-3553-04  2    3    3
S-3553-05  2    3    3
S-3553-06  2    3    3
S-3553-07  3    3    3
S-3553-08  3    4    4
S-3553-09  2    2    2
S-3553-10  3    3    3
S-3553-11  4    4    4

S-3554-01  3    4    4
S-3554-02  2    2    3
S-3554-03  2    3    3
S-3554-04  4    4    4
S-3554-05  2    2    3
S-3554-06  4    4    4
S-3554-07  3    3    3
S-3554-08  3    3.5  4
S-3554-09  4    4    4
S-3554-10  3.5  4    4
S-3554-11  3    4    4
S-3554-12  3    4    4

S-3555-01  2    3    3
S-3555-02  3    2    2
S-3555-03  3    3    3
S-3555-04  2    3    3
S-3555-05  4    4    4
S-3555-06  4    4    4
S-3555-07  2    2.5  2
S-3555-08  4    4    4
S-3555-09  3    4    4
S-3555-10  3    3    3
S-3555-11  1    2    1

S-3556-01  1    1    1
S-3556-02  3    3    3
S-3556-03  1    1    1
S-3556-04  2    1    1
S-3556-05  2    1    1
S-3556-06  1    2    2
S-3556-07  3    2    2
S-3556-08  3    2    2
S-3556-09  1    1    1
S-3556-10  1    1    1
S-3556-11  1    1    1
S-3556-12  1    2    1
S-3556-13  2    2    2

S-3567-01  4    4    4
S-3567-02  4    4    4
S-3567-03  4    4    4
S-3567-04  4    4    4
S-3567-05  4    4    4

S-3568-01  2    3    3
S-3568-02  2    3    2
S-3568-03  2    3    2
S-3568-04  2    2    2
S-3568-05  4    4    4
S-3568-06  2    1    1
S-3568-07  2    2    2
S-3568-08  1    2    2
S-3568-09  1    2    1
S-3568-10  1    2    2

S-3570-01  0    1    1
S-3570-02  0    1    0
S-3570-03  1    0.5  1
S-3570-04  0    0    0
S-3570-05  2.5  2    3
S-3570-06  1    1    1
S-3570-07  2    2    2
S-3570-08  4    4    4
S-3570-09  1    1    2
S-3570-10  0    1    0
S-3570-11  2    1    2

S-3571-01  3    4    4
S-3571-02  2    3    3
S-3571-03  2    3    3
S-3571-04  1    2    1
S-3571-05  3    3    3
S-3571-06  2    3    3
S-3571-07  2    4    4
S-3571-08  2    3.5  3
S-3571-09  2    2    2
S-3571-10  2    3    3
S-3571-11  2    2    2

S-3572-01  3    3    3
S-3572-02  3    3    4
S-3572-03  3    3    3
S-3572-04  0    1    1
S-3572-05  1    2    2
S-3572-06  2    2.5  2
S-3572-07  2    1    2
S-3572-08  1    1    1
S-3572-09  4    3    4
S-3572-10  1    0    0
S-3572-11  2    1    1
S-3572-12  2    2    2

S-3573-01  2    3    3
S-3573-02  2    2    2
S-3573-03  2    2    2
S-3573-04  3    3    3
S-3573-05  1    1    1
S-3573-06  2    1    1
S-3573-07  2    1    2
S-3573-08  1    0    1
S-3573-09  2    4    4
S-3573-10  2    4    4
S-3573-11  2.5  2    2

S-3574-01  1    0    0
S-3574-02  1    0    0
S-3574-03  1    0    0
S-3574-04  1    0    1
S-3574-05  1    1    1
S-3574-06  0    0    0
S-3574-07  1    1    1
S-3574-08  1    0    0
S-3574-09  1    0    0
S-3574-10  2    4    4
S-3574-11  1    3    3
S-3574-12  1    2    2

S-3575-01  1    1    1
S-3575-02  2    1    2
S-3575-03  2    2    2
S-3575-04  2    1    2
S-3575-05  2.5  2    3
S-3575-06  1    1    1
S-3575-07  1    1    1
S-3575-08  2    1    2
S-3575-09  1    2.5  2
S-3575-10  1    1    1
S-3575-11  1    1    1

S-3576-01  2    2    2
S-3576-02  1    2    1
S-3576-03  2    2    2
S-3576-04  1    1    2
S-3576-05  2    2    2
S-3576-06  1    0    1
S-3576-07  2    2    2
S-3576-08  2    2    2
S-3576-09  1    1    1
S-3576-10  2    1    2

S-3577-01  2    2    2
S-3577-02  1    1    1
S-3577-03  1    1    1
S-3577-04  2    2    2
S-3577-05  1    1    2
S-3577-06  2    2    2
S-3577-07  1    1    1
S-3577-08  1    2    2
S-3577-09  1    1    1
S-3577-10  2    2    2
S-3577-11  1    1    1

S-3578-01  2    2    2
S-3578-02  1    1    1
S-3578-03  2    2    2
S-3578-04  2    1    2
S-3578-05  1    1    1
S-3578-06  0    0    0
S-3578-07  1    3    2
S-3578-08  2    2    2
S-3578-09  0    1    1
S-3578-10  1    1    1
S-3578-11  1    1.5  1
S-3578-12  1    1    1

S-3579-01  1    3    2
S-3579-02  2    3    3
S-3579-03  2    2    2
S-3579-04  2    2    2
S-3579-05  2.5  2    2
S-3579-06  1    1    2
S-3579-07  2    1    2
S-3579-08  3    1    3
S-3579-09  3    3    3
S-3579-10  3    2    3
S-3579-11  2    1    1

S-3580-01  1    1    1
S-3580-02  2    2    2
S-3580-03  2    3    2
S-3580-04  2    4    3
S-3580-05  1    1    1
S-3580-06  1    1    1
S-3580-07  1    0    0
S-3580-08  1    0    0
S-3580-09  0    1    1
S-3580-10  1    1    1
S-3580-11  1    1    1

S-3589-01  1    2    2
S-3589-02  1    1    1
S-3589-03  2    1    2
S-3589-04  2    1    2
S-3589-05  2    2    2
S-3589-06  2    4    3
S-3589-07  2    2    2
S-3589-08  4    4    4
S-3589-09  1    1    2
S-3589-10  1    1    1
S-3589-11  1    1    1
S-3589-12  1    2    1

S-3590-01  2    1    2
S-3590-02  1    1    1
S-3590-03  2    2    2
S-3590-04  2    2    2
S-3590-05  3    4    3
S-3590-06  1    2    2
S-3590-07  1    1    1
S-3590-08  2    2    2
S-3590-09  1    2    2
S-3590-10  1    1    1
S-3590-11  0    0    0
S-3590-12  0    1    0
S-3590-13  0    0    0

S-3591-01  1    1    1
S-3591-02  1    2    1
S-3591-03  1    2    1
S-3591-04  1    2    2
S-3591-05  0    0    0
S-3591-06  1    1    1
S-3591-07  3    3    3
S-3591-08  1    2    2
S-3591-09  1    1    1
S-3591-10  1    1    1
S-3591-11  1    1    2
S-3591-12  3    2    3

S-3592-01  0    0    0
S-3592-02  0    0    0
S-3592-03  0    0    0
S-3592-04  0    0    0
S-3592-05  0    0    0
S-3592-06  0    0    0
S-3592-07  1    1    1
S-3592-08  1    2    2
S-3592-09  1    2    2
S-3592-10  1    2    1

S-3593-01  1    2    2
S-3593-02  1    1    1
S-3593-03  1    1    1
S-3593-04  2    2    2
S-3593-05  1    2    2
S-3593-06  2    2    2
S-3593-07  2    2    2
S-3593-08  4    4    4
S-3593-09  2    1    2
S-3593-10  2.5  1    3
S-3593-11  0    0    0

S-3594-01  1    1    1
S-3594-02  1    2    1
S-3594-03  0    0    0
S-3594-04  0    0    0
S-3594-05  0    0    0
S-3594-06  1    1    1
S-3594-07  0    1    1
S-3594-08  0    1    1
S-3594-09  0    1    1
S-3594-10  2    2    2
S-3594-11  2    3    3
S-3594-12  1    2    1
S-3594-13  1    2    2

S-3595-01  1    1    1
S-3595-02  1    1    1
S-3595-03  1    2    2
S-3595-04  2    2    2
S-3595-05  3    4    3
S-3595-06  0    0    0
S-3595-07  0    1    1
S-3595-08  0    1    1
S-3595-09  3    3    3
S-3595-10  2    2    2
S-3595-11  1    1    1

S-3596-01  0    1    1
S-3596-02  1    1    1
S-3596-03  0    1    1
S-3596-04  0    1    1
S-3596-05  1    2    2
S-3596-06  0    0    1
S-3596-07  0    0    0
S-3596-08  0    1    0
S-3596-09  1    0    0
S-3596-10  2    2    2
S-3596-11  0    1    1

S-3597-01  1    1    1
S-3597-02  1    2    2
S-3597-03  0.5  1    1
S-3597-04  3    4    3
S-3597-05  0    1    1
S-3597-06  0    1    0
S-3597-07  0    1    0
S-3597-08  1    2    2
S-3597-09  2    1    2
S-3597-10  1    2    2
S-3597-11  1    1    1

S-3598-01  0    0    0
S-3598-02  0    0.5  0
S-3598-03  1    1    1
S-3598-04  1    2    2
S-3598-05  1    2    2
S-3598-06  1    1    1
S-3598-07  0.5  1    1
S-3598-08  0    1    1
S-3598-09  1    2    2
S-3598-10  0    0    0
S-3598-11  1    0    1
S-3598-12  1.5  1    1
S-3598-13  2    2    2

S-3599-01  2    2    2
S-3599-02  1    1    1
S-3599-03  1    2    2
S-3599-04  0    0    0
S-3599-05  0    0    0
S-3599-06  2    2    2
S-3599-07  2    2    2
S-3599-08  0.5  0    1
S-3599-09  1    0    1
S-3599-10  1    1    1
S-3599-11  1    0    0

S-3600-01  1    1.5  2
S-3600-02  2    2    2
S-3600-03  1    1    1
S-3600-04  0    0    0
S-3600-05  1    1    1
S-3600-06  1    0    1
S-3600-07  1    1    1
S-3600-08  1    1    1
S-3600-09  0.5  0    0
S-3600-10  1    0    1
S-3600-11  1    2    1
S-3600-12  2    2    1
S-3600-13  2    1    1

S-3668-01  1    0    1
S-3668-02  1    1    1
S-3668-03  1    2    2
S-3668-04  1    2    2
S-3668-05  0    2    2
S-3668-06  1    1    1
S-3668-07  1    1    1
S-3668-08  0    0    0
S-3668-09  0    1    0
S-3668-10  0    1    1
S-3668-11  0    0    0

S-3669-01  1    1    1
S-3669-02  1    1    1
S-3669-03  1    2    2
S-3669-04  1    1    1
S-3669-05  1    0    0
S-3669-06  2    2    2
S-3669-07  1    1    1
S-3669-08  1    1    1
S-3669-09  0    1    0
S-3669-10  0    1    0
S-3669-11  0    0    0

S-3670-01  1    1    1
S-3670-02  0    2    2
S-3670-03  1    1    1
S-3670-04  0    1    1
S-3670-05  1    1    1
S-3670-06  1    1    1
S-3670-07  0    1    1
S-3670-08  0    1    0
S-3670-09  0    1    0
S-3670-10  1    0    1
S-3670-11  2    2    2
S-3670-12  1    0    1

S-3671-01  1    0    1
S-3671-02  1    1    1
S-3671-03  1    1    1
S-3671-04  1    1    1
S-3671-05  2    2    2
S-3671-06  1    0    1
S-3671-07  1    0    0
S-3671-08  1    1    1
S-3671-09  0    0    0
S-3671-10  1    1    1

S-3672-01  1    1    1
S-3672-02  1    1    1
S-3672-03  1    0    1
S-3672-04  1    2    1
S-3672-05  1    1    1
S-3672-06  0    0    0
S-3672-07  1    1    1
S-3672-08  0    2    2
S-3672-09  0    0    1
S-3672-10  1    1    1
S-3672-11  0    0    1
S-3672-12  1    1    0

S-3673-01  1    0    0
S-3673-02  0    0    0
S-3673-03  0    0    0
S-3673-04  0    0    0
S-3673-05  0    0    0
S-3673-06  1    0    1
S-3673-07  1    1    1
S-3673-08  0    0    0
S-3673-09  1    1    1
S-3673-10  0    1    0
"""


def parse_scores(raw: str) -> dict:
    """
    Parse RAW_SCORES into a dict:
        { 'S-3536-01': {'edema': 1.5, 'necrosis': 2.0, 'inflammation': 2.0, 'total': 5.5}, ... }
    Total is recalculated as edema + necrosis + inflammation.
    """
    scores = {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            continue
        sample_id, e, n, i = parts
        try:
            edema        = float(e)
            necrosis     = float(n)
            inflammation = float(i)
        except ValueError:
            continue
        total = round(edema + necrosis + inflammation, 4)
        scores[sample_id] = {
            "edema":        edema,
            "necrosis":     necrosis,
            "inflammation": inflammation,
            "total":        total,
        }
    return scores


def filename_to_sample_id(filename: str) -> str | None:
    """
    Convert an image filename to a sample ID, e.g.:
        'S-3536-10x_Image001_RAW_ch00.tif'  →  'S-3536-01'
        'S-3589-10X_Image012_RAW_ch00.tif'  →  'S-3589-12'

    Returns None if the filename doesn't match the expected pattern.
    """
    stem = filename  # work with the raw filename string
    # Strip extension
    if stem.lower().endswith(".tif"):
        stem = stem[:-4]

    # Must contain '_Image'
    img_marker = "_Image"
    idx = stem.find(img_marker)
    if idx == -1:
        # try case-insensitive
        lower = stem.lower()
        idx = lower.find("_image")
        if idx == -1:
            return None
        img_marker = stem[idx: idx + 6]  # preserve original case slice

    prefix = stem[:idx]         # e.g. 'S-3536-10x'
    rest   = stem[idx + len(img_marker):]  # e.g. '001_RAW_ch00'

    # Extract numeric part of image number
    num_str = ""
    for ch in rest:
        if ch.isdigit():
            num_str += ch
        else:
            break
    if not num_str:
        return None

    image_num = int(num_str)   # 001 → 1

    # Derive experiment ID: take parts before the magnification suffix
    # prefix is like 'S-3536-10x' or 'S-3589-10X'
    # Split on '-' and take first two parts
    parts = prefix.split("-")
    if len(parts) < 2:
        return None
    experiment_id = f"{parts[0]}-{parts[1]}"  # 'S-3536'

    # Build sample ID with zero-padded 2-digit image number
    sample_id = f"{experiment_id}-{image_num:02d}"
    return sample_id


def main():
    print("=" * 60)
    print("AP Dataset Preparation Script")
    print("=" * 60)

    # ── 1. Parse scores ──────────────────────────────────────────
    scores = parse_scores(RAW_SCORES)
    print(f"\n[1] Parsed {len(scores)} labeled sample entries from scoring table.")

    # ── 2. Create destination directory ──────────────────────────
    DEST_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[2] Destination directory: {DEST_IMAGE_DIR}")

    # ── 3. Scan source folders ────────────────────────────────────
    print(f"\n[3] Scanning source directory: {AP_SOURCE_DIR}")

    csv_rows            = []   # rows that will go into the CSV
    copied_count        = 0
    skipped_no_label    = 0
    skipped_already     = 0
    unmatched_filenames = []   # images where parsing failed

    # Collect all subfolders (case-insensitive folder handling is automatic
    # since we just iterate whatever the filesystem gives us)
    source_folders = sorted(
        [d for d in AP_SOURCE_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.name.upper()
    )

    for folder in source_folders:
        # Iterate files inside the folder
        for img_file in sorted(folder.iterdir()):
            # Skip subdirectories (including MetaData/)
            if img_file.is_dir():
                continue
            # Skip non-.tif files (e.g. .DS_Store)
            if not img_file.suffix.lower() == ".tif":
                continue

            # Map filename → sample ID
            sample_id = filename_to_sample_id(img_file.name)
            if sample_id is None:
                unmatched_filenames.append(img_file.name)
                continue

            # Look up label
            if sample_id not in scores:
                skipped_no_label += 1
                continue  # Do NOT copy unlabeled images

            # Copy to destination
            dest_path = DEST_IMAGE_DIR / img_file.name
            if dest_path.exists():
                skipped_already += 1
            else:
                shutil.copy2(img_file, dest_path)
                copied_count += 1

            # Add to CSV rows
            label = scores[sample_id]
            csv_rows.append({
                "filename":     img_file.name,
                "edema":        label["edema"],
                "necrosis":     label["necrosis"],
                "inflammation": label["inflammation"],
                "total":        label["total"],
            })

    # ── 4. Write CSV ──────────────────────────────────────────────
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Sort rows by filename for reproducibility
    csv_rows.sort(key=lambda r: r["filename"].upper())

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["filename", "edema", "necrosis", "inflammation", "total"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    # ── 5. Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Images copied to destination     : {copied_count}")
    print(f"  Images already present (skipped) : {skipped_already}")
    print(f"  Images skipped (no label)        : {skipped_no_label}")
    print(f"  Filenames that couldn't be parsed: {len(unmatched_filenames)}")
    print(f"  CSV rows written                 : {len(csv_rows)}")
    print(f"\n  Output CSV  : {OUTPUT_CSV}")
    print(f"  Images dir  : {DEST_IMAGE_DIR}")

    # Check for labeled samples that had no matching images
    found_samples = set()
    for row in csv_rows:
        sid = filename_to_sample_id(row["filename"])
        if sid:
            found_samples.add(sid)
    missing_from_disk = set(scores.keys()) - found_samples
    if missing_from_disk:
        print(f"\n  ⚠  {len(missing_from_disk)} labeled sample(s) had NO matching image on disk:")
        for s in sorted(missing_from_disk):
            print(f"       {s}")

    if unmatched_filenames:
        print(f"\n  ⚠  Filenames that couldn't be parsed ({len(unmatched_filenames)}):")
        for f in unmatched_filenames:
            print(f"       {f}")

    print("\n✅  Done!")


if __name__ == "__main__":
    main()
