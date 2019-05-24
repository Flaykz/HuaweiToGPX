

# HuaweiToGPX
Export HiTrack Huawei file from Watch GT to GPX file

>Thanks to https://github.com/aricooperdavis/Huawei-TCX-Converter for the inspiration.

## Description
Users of Huawei Watches/Bands sync their fitness data with the Huawei Health App. It's actually impossible to convert exercices to GPX directly from the application. 

This program allows you to convert raw files from the app and generate GPX files for use in your tracking app of choice (e.g. Strava). The outputted GPX files will contain timestamped GPS, altitude, heart-rate, and speed data where available.

## How to get the HiTrack Files:
Open the Huawei Health app and open the exercise that you want to convert to view it's trajectory. This ensures that its `HiTrack` file is generated.

**If you have a rooted phone:**
* you can simply navigate to: `data/data/com.huawei.health/files/` where you should find a number of files prefixed `HiTrack`.

**If you have an unrooted phone then:**
* Download the Huawei Backup App onto your phone.
* Start a new unencrypted backup of the Huawei Health app data to your external storage (SD Card)
* Navigate to `Huawei/Backup/***/backupFiles/***/` and copy `com.huawei.health.tar` to your computer.
* Untar the file and navigate to `com.huawei.health/files/` and you should should see a number of `HiTrack` files.

## How to use the Huawei GPX Converter:
Download the script and save it as a Python script in the same folder as your `HiTrack` file.
To be sure to have all necessary packages, do a `pip3 install -r requirements.txt`

The tool is run on the command line. Without arguments, every `HiTrack` files present in the same fold than the scrip will be processed and transformed in a `GPX` file renamed with this rule :
> ddmmyyyy_hhmmss_hhmmss.gpx 

where the two hours are the start and end time of exercice. You can alternatively pass a list of file to process but they have to get the original HiTrack name.

### Other command line arguments:
-d or --debug : Allow to see more informations during processing

## TO DO
 - [x] Debug options to show more informations
 - [ ] Check compatibility with differents devices
 - [ ] Get the choice between altitude from file and from google for example
 - [ ] Get the choice to grab hiTrack files from subdirectories
