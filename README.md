# autofill_ndar_image03_template

This Python script will auto-populate an NDAR "image 03" template (as defined here: [Image](https://ndar.nih.gov/data_structure.html?short_name=image03/) ) given a list of data directories, a list of subject demographics, and possibly a list of NDAR experiments (in the case of functional MRI data). Each neuroimaging dataset will need to have a [BXH/XCEDE header](https://www.nitrc.org/projects/bxh_xcede_tools/), and must be in NRRD format (.nrrd) if it's a DTI dataset, and compressed NIFTI (.nii.gz) otherwise (structural, fMRI and/or resting state fMRI). 
