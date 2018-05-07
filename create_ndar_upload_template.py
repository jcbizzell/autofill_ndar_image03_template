#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys
import os
import csv
import calendar
from datetime import datetime
import re
import lxml.etree as ET

# ------------------
# Change items below
# ------------------

# What is the base directory where the scan list, demographics and output .csv template will be located
exppath = "/mnt/BIAC/munin.dhe.duke.edu/Belger/ADOLSTRESS.01/Scripts/NDAR_Upload/GitVersion"
# What is the full file name of the scan directory list; this also reads that file
scanlist = csv.reader(open(os.path.join(exppath,"ExampleFiles","scan_dir_list.csv"),"rb"),delimiter=",")
# Load and read the demographics file
demofile = open(os.path.join(exppath,"ExampleFiles","demographics.csv"),"rb")
demos = csv.reader(demofile, delimiter = ',')
# Load and read the experiments description file
expfile = open(os.path.join(exppath,"ExampleFiles","yourstudy_experiment_list.csv"),"rb")
exps = csv.reader(expfile, delimiter = ',')
# Where are the FSL motion outlier CSVs for the functional data
motoutpath=os.path.join(exppath,"ExampleFiles","motion_outliers")
# Where would the DTIPrep-ed data be?
dtipath=os.path.join(exppath,"ExampleFiles","DTIPrep_logs")
# Where will the output CSV template be saved
outcsv = os.path.join(exppath,"ndar_image03_template_"+"{:%Y%m%d_%H_%M_%S}".format(datetime.now())+".csv")
# Which image series BXH "descriptions" should be included
funclist = ['sensespiral fMRI','Sag 2sh-MB resting fMRI']
dtilist = ['Ax DTI']
otherlist = ['SC:Ax FSPGR 3D']
# What is the root path to data on Linux (need trailing slash)
rootlin = "/mnt/BIAC/munin.dhe.duke.edu/"
# What is the root path to data on Windows (need escape slashes and trailing slash)
rootwin = "\\\\Munin\\Data\\"

# ---------------------------
# Possibly change items below
# ---------------------------

# List of all of the element names in the NDAR Data Dictionary for the image_03 type
# More info here: https://ndar.nih.gov/data_structure.html?short_name=image03
ndar_image03_elements=['subjectkey','src_subject_id','interview_date','interview_age','gender','comments_misc','image_file','image_thumbnail_file','image_description','experiment_id','scan_type','scan_object','image_file_format','data_file2','data_file2_type','image_modality','scanner_manufacturer_pd','scanner_type_pd','scanner_software_versions_pd','magnetic_field_strength','mri_repetition_time_pd','mri_echo_time_pd','flip_angle','acquisition_matrix','mri_field_of_view_pd','patient_position','photomet_interpret','receive_coil','transmit_coil','transformation_performed','transformation_type','image_history','image_num_dimensions','image_extent1','image_extent2','image_extent3','image_extent4','extent4_type','image_extent5','extent5_type','image_unit1','image_unit2','image_unit3','image_unit4','image_unit5','image_resolution1','image_resolution2','image_resolution3','image_resolution4','image_resolution5','image_slice_thickness','image_orientation','qc_outcome','qc_description','qc_fail_quest_reason','decay_correction','frame_end_times','frame_end_unit','frame_start_times','frame_start_unit','pet_isotope','pet_tracer','time_diff_inject_to_image','time_diff_units','pulse_seq','slice_acquisition','software_preproc','study','week','experiment_description','visit','slice_timing','bvek_bval_files','bvecfile','bvalfile','deviceserialnumber','procdate','visnum']

# ------------------------------------
# Shouldn't need to change items below
# ------------------------------------

# Create a function to convert day number in a year to months in that year/round up if day in last half of month
def daynum_to_date(year, daynum):
    month = 1
    day = daynum
    while month < 13:
        month_days = calendar.monthrange(year, month)[1]
        if day <= month_days:
            if day <= month_days/2:
                return month
            else: 
                return (month+1)
        day -= month_days
        month += 1
    raise ValueError('{} does not have {} days'.format(year, daynum))

# Initialize other variables
nspace={'b': 'http://www.biac.duke.edu/bxh'}
# Make all values in include lists lowercase
funclist = [x.lower() for x in funclist]
dtilist = [x.lower() for x in dtilist]
otherlist = [x.lower() for x in otherlist]
# Search the experiment file to find number of experiment groups
num_exp_grps=0
grp=0
expfile.seek(0)
for e in exps:
    try:
        grp=int(e[3])
        if grp > num_exp_grps:
            num_exp_grps = int(e[3])
    except ValueError:
        pass
# Open the output csv template
outcsv = open(outcsv,'w+')
# Write the template header
outcsv.write('image,03\r\n')
for count, elem in enumerate(ndar_image03_elements):
    if count == 0:
        outcsv.write(elem)
    else:
        outcsv.write(','+elem)
outcsv.write('\r\n')

# Loop through the list of scans
for scan in scanlist:
    # Reset the search to the beginning of demographics file
    demofile.seek(0)
    # Initialize some variables
    exp_orders = [1]*num_exp_grps
    # Loop through the demographics searching for subject scan ID
    foundscan = False
    for row in demos:
        # If scan id found in demographics file
        if row[1] in scan[0]:
            print('Working on '+row[6]+' dir '+scan[0])
            foundscan = True
            # Load the motion outliers file
            motoutfile = open(os.path.join(motoutpath,row[0],"mot_out_stats.csv"),"rb")
            mot_out = csv.reader(motoutfile, delimiter = ',')
            # Convert YYYYMMDD to MM/DD/YYYY
            scandate=datetime.strptime(row[1][0:8], '%Y%m%d').strftime('%m/%d/%Y')
            # Convert age to number of months
            age=float(row[5])
            age_in_m = str((int(age)*12)+(daynum_to_date(int(row[1][0:4]), round((age-int(age))*365))))
            # Loop through the files in the directories list looking for BXH files
            for count, fname in enumerate(sorted(os.listdir(scan[0])), start=1):
                if fname.endswith(".bxh"):
                    # print('Loading '+os.path.join(scan[0],fname))
                    # xmlh = bxh.load(os.path.join(scan[0],fname))
                    doc = ET.parse(os.path.join(scan[0],fname))
                    root = doc.getroot()
                    datarec = root.find('b:datarec',namespaces=nspace)
                    acqelem = root.find('b:acquisitiondata', namespaces=nspace)
                    #print('finished loading')
                    imdesc=acqelem.findtext('b:description',namespaces=nspace).lower()
                    if imdesc in funclist+dtilist+otherlist:
                        # Initialize variables
                        print('ADDING '+imdesc)
                        isfunc=False
                        isdti=False
                        # Initialize the output string
                        outstr = ['']*len(ndar_image03_elements)
                        if imdesc in funclist: 
                            isfunc = True
                            # Find the number of timepoints
                            numtp=datarec.findall('b:dimension',namespaces=nspace)[3].find('b:size',namespaces=nspace).text
                            # Search the experiment file to find correct experiment
                            expfile.seek(0)
                            for e in exps:
                                if imdesc == e[5].lower() and numtp in e[6]:
                                    if exp_orders[int(e[3])-1] == int(e[4]):
                                        outstr[ndar_image03_elements.index('experiment_description')]=e[1]
                                        outstr[ndar_image03_elements.index('experiment_id')]=e[2]
                                        exp_orders[int(e[3])-1]+=1
                                        break
                        if imdesc in dtilist:
                            isdti = True

                        # -----------------------------------------
                        # Fill in the elements shared by all images
                        # -----------------------------------------

                        # Subject demographics data
                        outstr[ndar_image03_elements.index('subjectkey')]=row[6]  # From column 7 in demographcis
                        outstr[ndar_image03_elements.index('src_subject_id')]=row[0]  # From column 1 in demographics
                        outstr[ndar_image03_elements.index('interview_date')]=scandate  # Calculated above
                        outstr[ndar_image03_elements.index('interview_age')]=age_in_m  # Calcluated above
                        outstr[ndar_image03_elements.index('gender')]=row[3]  # From column 4 in demographics
                        outstr[ndar_image03_elements.index('visit')]='Visit '+str(row[7])  # From column 8 in demographics
                        outstr[ndar_image03_elements.index('visnum')]=str(int(row[7])-1)   #   "    "
                        # PUT GROUP TYPE IN COMMENTS?

                        # Initialize some dimension variables
                        numdims = len(datarec.findall('b:dimension',namespaces=nspace))
                        dimsz=[0]*numdims
                        dimres=[0]*numdims
                        dimunits=['']*numdims
                        # Populate dimension variables
                        for count, dim in enumerate(datarec.findall('b:dimension',namespaces=nspace)):
                            dimsz[count] = int(dim.find('b:size',namespaces=nspace).text)
                            try: 
                                dimres[count] = float(dim.find('b:spacing',namespaces=nspace).text)
                            except AttributeError:
                                if isdti:
                                    dimres[count] = None
                                else: 
                                    dimres[count] = 0
                            try: 
                                dimunits[count] = dim.find('b:units',namespaces=nspace).text
                            except AttributeError: 
                                dimunits[count] = 'N/A'

                        # MRI dimension parameters
                        outstr[ndar_image03_elements.index('image_num_dimensions')]=str(numdims)
                        outstr[ndar_image03_elements.index('image_slice_thickness')]=str(round(dimres[2],4))
                        for count in range(0, numdims):
                            # Fill in image dimension sizes
                            exec('outstr[ndar_image03_elements.index("image_extent'+str(count+1)+'")]=str(dimsz[count])')
                            # Fill in the image dimension units
                            if dimunits[count] == "mm": 
                                exec('outstr[ndar_image03_elements.index("image_unit'+str(count+1)+'")]="Millimeters"')
                            elif any(dimunits[count] in x  for x in ["ms" "msec"]):
                                exec('outstr[ndar_image03_elements.index("image_unit'+str(count+1)+'")]="Milliseconds"')
                            elif isdti:
                                exec('outstr[ndar_image03_elements.index("image_unit'+str(count+1)+'")]="Diffusion gradient"')
                            else: 
                                ostr = dimunits[count]
                            # Fill in the image dimension resolution
                            if dimres[count] == None:
                                exec('outstr[ndar_image03_elements.index("image_resolution'+str(count+1)+'")]=""')
                            else: 
                                exec('outstr[ndar_image03_elements.index("image_resolution'+str(count+1)+'")]=str(round(dimres[count],4))')
                            # Fill in the image dimension type description, if num dim >= 4
                            if count == 3:
                                if isfunc:
                                    outstr[ndar_image03_elements.index('extent4_type')]='Time'
                                elif isdti:
                                    outstr[ndar_image03_elements.index('extent4_type')]='Gradient Number'
                                else:
                                    outstr[ndar_image03_elements.index('extent4_type')]='Unknown'
                            if count == 4:
                                outstr[ndar_image03_elements.index('extent5_type')]='Uunknown'
                            
                        # MRI subject, scanner, acquisition info/same field for every scan type
                        outstr[ndar_image03_elements.index('scan_object')]='Live'
                        outstr[ndar_image03_elements.index('image_modality')]='MRI'
                        outstr[ndar_image03_elements.index('scanner_manufacturer_pd')]='GE Medical'
                        outstr[ndar_image03_elements.index('scanner_type_pd')]='MR750'
                        outstr[ndar_image03_elements.index('scanner_software_versions_pd')]='DV24.0_R01_1344.a'
                        outstr[ndar_image03_elements.index('magnetic_field_strength')]='3'
                        tr = str(float(acqelem.findtext('b:tr',namespaces=nspace))/1000)  # Convert to seconds
                        outstr[ndar_image03_elements.index('mri_repetition_time_pd')]=tr
                        outstr[ndar_image03_elements.index('mri_echo_time_pd')]=acqelem.findtext('b:te',namespaces=nspace)
                        outstr[ndar_image03_elements.index('flip_angle')]=acqelem.findtext('b:flipangle',namespaces=nspace)
                        outstr[ndar_image03_elements.index('acquisition_matrix')]=acqelem.findtext('b:acquisitionmatrix',namespaces=nspace)
                        fov_x=round(dimres[0]*dimsz[0])
                        fov_y=round(dimres[1]*dimsz[1])
                        outstr[ndar_image03_elements.index('mri_field_of_view_pd')]=str(fov_x)+' '+str(fov_y)
                        outstr[ndar_image03_elements.index('patient_position')]='HFS'
                        outstr[ndar_image03_elements.index('photomet_interpret')]='Monochrome2'
                        outstr[ndar_image03_elements.index('receive_coil')]=acqelem.findtext('b:receivecoilname',namespaces=nspace)
                        outstr[ndar_image03_elements.index('transmit_coil')]='Body'
                        outstr[ndar_image03_elements.index('transformation_performed')]='No'
                        outstr[ndar_image03_elements.index('image_history')]='BXH/XCEDE Tools'
                        com = datarec.getchildren()[0]
                        if 'AUTOGEN' in com.text:
                            orientation = re.search('(sagittal|coronal|axial)',com.text).group()
                        outstr[ndar_image03_elements.index('image_orientation')]=orientation.title()
                        outstr[ndar_image03_elements.index('pulse_seq')]=acqelem.findtext('b:psdname',namespaces=nspace)
                        outstr[ndar_image03_elements.index('software_preproc')]='BXH/XCEDE Utilities (1.11.8)'
                        outstr[ndar_image03_elements.index('study')]=acqelem.findtext('b:studyid',namespaces=nspace)
                        outstr[ndar_image03_elements.index('deviceserialnumber')]='0000000919684MR5'


                        # -------------------------------------------------
                        # Fill in the elements for specific types of images
                        # -------------------------------------------------
                        # If dataset is fMRI
                        if isfunc: 
                            outstr[ndar_image03_elements.index('image_description')]='fMRI'
                            outstr[ndar_image03_elements.index('scan_type')]='fMRI'
                            # Get the filename and convert it to Windows format
                            niftifname=fname[:-3]+'nii.gz'
                            winpath = scan[0].replace(rootlin,rootwin).replace('/','\\')
                            outstr[ndar_image03_elements.index('image_file')]=winpath+'\\'+niftifname
                            outstr[ndar_image03_elements.index('image_file_format')]='NIFTI'
                            # Loop through the motion outliers file searching for NIFTI file
                            motoutfile.seek(0)
                            num_bad_vols = 0
                            for mot_outs in mot_out:
                                if mot_outs[0] == niftifname:
                                    num_bad_vols = mot_outs[2]
                                    break
                            percent_bad=100*float(num_bad_vols)/dimsz[3]
                            # Find out if the data is good, bad or questionable
                            if percent_bad <= 15: 
                                outstr[ndar_image03_elements.index('qc_outcome')]='pass'
                            elif 15 < percent_bad <= 25:
                                outstr[ndar_image03_elements.index('qc_outcome')]='questionable'
                            else:
                                outstr[ndar_image03_elements.index('qc_outcome')]='fail'
                                outstr[ndar_image03_elements.index('qc_fail_quest_reason')]='Too many volumes removed'
                            # Write the QC description
                            outstr[ndar_image03_elements.index('qc_description')]='Used FSL_MOTION_OUTLIERS to calc RMS intensity diff to find % bad volumes - PASS <= 15%; QUEST <= 25%; FAIL > 25%'
                            # Write the slice acquisition order
                            slicearray = [0]*dimsz[2]
                            if acqelem.findtext('b:sliceorder',namespaces=nspace)[0:3] == '2,4':
                                outstr[ndar_image03_elements.index('slice_acquisition')]='3'
                                slicearray[0:dimsz[2]/2] = range(1,dimsz[2],2)
                                slicearray[dimsz[2]/2:] = range(0,dimsz[2],2)
                            elif acqelem.findtext('b:sliceorder',namespaces=nspace)[0:3] == '1,2':
                                outstr[ndar_image03_elements.index('slice_acquisition')]='1'
                                slicearray = range(0,dimsz[2])
                            elif acqelem.findtext('b:sliceorder',namespaces=nspace)[0:1] == str(dimsz[2]):
                                outstr[ndar_image03_elements.index('slice_acquisition')]='2'
                                slicearray = range((dimsz[2]-1),-1,-1)
                            else: 
                                outstr[ndar_image03_elements.index('slice_acquisition')]='4'
                                slicearray[0:dimsz[2]/2] = range(0,dimsz[2],2)
                                slicearray[dimsz[2]/2:] = range(1,dimsz[2],2)
                            slicearrstr = '[ '
                            for s in slicearray:
                                slicearrstr = slicearrstr+str(round(float(s)*(dimres[3]/dimsz[2]),2))+' '
                            slicearrstr = slicearrstr+']'
                            outstr[ndar_image03_elements.index('slice_timing')]=slicearrstr

                        # If dataset is DTI
                        elif isdti: 
                            outstr[ndar_image03_elements.index('image_description')]='DTI'
                            outstr[ndar_image03_elements.index('scan_type')]='MR diffusion'
                            # Get the filename and convert it to Windows format
                            niftifname=fname[:-3]+'nrrd'
                            winpath = scan[0].replace(rootlin,rootwin).replace('/','\\')
                            outstr[ndar_image03_elements.index('image_file')]=winpath+'\\'+niftifname
                            outstr[ndar_image03_elements.index('image_file_format')]='NRRD'
                            outstr[ndar_image03_elements.index('image_resolution4')]='1'
                            percent_bad = 0
                            for line in open(os.path.join(dtipath,row[0],'dti_55dir_QCReport.txt')):
                                if "Too many" in line:
                                    percent_bad = 20
                            if percent_bad < 20:
                                outstr[ndar_image03_elements.index('qc_outcome')]='pass'
                            else:
                                outstr[ndar_image03_elements.index('qc_outcome')]='fail'
                                outstr[ndar_image03_elements.index('qc_fail_quest_reason')]='More than 20% of gradients removed'
                            # Write the QC description
                            outstr[ndar_image03_elements.index('qc_description')]='DTIPrep'
                            
                            outstr[ndar_image03_elements.index('bvek_bval_files')]='Yes'

                        # If dataset is other
                        else:
                            outstr[ndar_image03_elements.index('image_description')]=imdesc
                            if "fspgr" in imdesc:
                                outstr[ndar_image03_elements.index('scan_type')]='MR structural (FSPGR)'
                            # Get the filename and convert it to Windows format
                            niftifname=fname[:-3]+'nii.gz'
                            winpath = scan[0].replace(rootlin,rootwin).replace('/','\\')
                            outstr[ndar_image03_elements.index('image_file')]=winpath+'\\'+niftifname
                            outstr[ndar_image03_elements.index('image_file_format')]='NIFTI'

                        #print(outstr)
                        # Write the output string to NDAR CSV template
                        for count, elem in enumerate(outstr):
                            if count == 0:
                                outcsv.write(elem)
                            else:
                                outcsv.write(','+elem)
                        outcsv.write('\r\n')

                    else:
                        print('Not adding '+imdesc)
            
            # Close the motion outliers file
            motoutfile.close()
            # Break out of the loop through demographics file if found
            break

    if not(foundscan):
        print('Found no demographics data for '+scan[0])

outcsv.close()


