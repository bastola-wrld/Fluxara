# Legacy research code

Not part of the product. Nothing here is imported by the API or by ingestion.

* `notebooks/`, `research/`: early experiments. The EPA "validation" in
  `04_validate_ghgrp.ipynb` fed the model random wind fields and is not a
  validation.
* `generate_stilt_data.py`, `train_model_local.py`: train the U-Net on
  synthetic Gaussian plumes.
* `tests/`: the old test suites for that code.
* `satellite_data_old/`: old sample tensors.

The model code itself is still in `fluxara/models` and `fluxara/training`
and needs `requirements_legacy.txt`.
