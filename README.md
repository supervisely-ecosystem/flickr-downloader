<div align="center" markdown>
<img src="https://live.staticflickr.com/2893/9775672575_594e5968e9.jpg"/>

# Download images from Flickr straight to a Supervisely dataset

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Overview</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

placeholder for ecosystem badge
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
placeholder for release badge
placeholder for views badge
placeholder for runs badge

</div>

## Overview
This app allows to download thousands of images from Flickr straight to a Supervisely dataset. After specifying a search query and some additional parameters (such as a license type, number of images, etc.) with only one click you can download images from Flickr and add them to a Supervisely dataset including meta information from Flickr (such as title, description, etc.).<br>
For example: you enter a search query "dog" and set the number of images to 1000. You can check the available licenses and meta information to download along with the images. After it, you can specify the project and the dataset to add the images (otherwise a new project and dataset will be created automatically). And now you only need to click "Download" and wait for the app to finish the job. After that, you will have a Supervisely dataset with up to 1000 images of dogs and all the meta information from Flickr that you have selected. For more details, see the [How To Run](#How-To-Run) section.<br>

## Preparation
To use this app, you need to obtain a Flickr API key. To do this, you need to register a Flickr account and then follow the instructions from the [Flickr API Keys](https://www.flickr.com/services/apps/create/apply/) page. You have two options to use your API key: you can use team files to store a .env file with the API key or you can enter the API key directly in the app GUI. Using team files is recommended as it is more convenient and faster, but you can choose the option that is more suitable for you.<br>

### Using team files
1. Create a .env file with the following content:<br>
```FLICKR_API_KEY=your_api_key```<br>
2. Upload the .env file to the team files.<br>
3. Right-click on the .env file, select "Run app" and choose the "Flickr Download" app.<br>
The app will be launched with the API key from the .env file and you won't need to enter it manually.<br>

### Entering the API key manually
1. Launch the app.<br>
2. You will notice that all cards of the app are locked except the "Flickr API Key" card. Enter your API key in the field and press the "Check connection button".<br>
3. If the connection is successful, all cards will be unlocked and you can proceed with the app. Otherwise, you will see an error message and you will need to enter the API key again.<br>
Now you can use the app. Note that in this case, you will need to enter the API key every time you launch the app.<br>

## How To Run
Note: in this section, we consider that you have already obtained the API key, and use it to run the app. If you haven't done it yet, see the [Preparation](#Preparation) section.<br>
So, here are the steps to download images from Flickr:<br>

**Step 1:** Enter the search query in the "Search query" field. You can use complex queries, for example, "dog and cat" or "blue car in the city".<br>
**Step 2:** Specify the license types of the images to download. You can select one or more license types, but at least one license type should be selected. Note that number of results depends on the license types. So more license types you select, the more results you will get.<br>
**Step 3:** After completing the previous steps, we recommend checking the available number of results with the "Check number of images" button. It will show you the total number of images with the specific search query and license types. If the number is smaller than you expected, you can change the search query or license types.<br>
** Step 4:** Now you need to enter the number of images to download. Note: due to a specific Flickr API search algorithm, the number of images you will get may be smaller than the number you have entered, because Flickr returns duplicates in the search results, and additionally, some of the images may be unavailable for download. So, we recommend entering a number of images that is slightly larger than you need (just from 1 to 2 percent).<br>
**Step 5:** You can also specify the starting image number for the search. It is useful if you want to continue downloading images to the existing dataset where you have already downloaded some images for the same (or similar) search query. So, this option allows you to skip specified amount of images in the search results. For example, if you have already downloaded 100 images for the search query "dog" and you want to continue downloading images, you can enter 100 in the "Starting image number" field and the app will skip the first 100 images in the search results.<br>
**Step 6:** In the next step, you can select the meta information to download along with the images. Note that information about the image owner and the license type will be always downloaded due to the license requirements. Other meta fields are optional.<br>
**Step 7:** Now you need to choose an upload method. There are two options available: upload images as links or as files. The first option won't download the image files to the dataset, it will just use the source file links. So, if the source file will be unavailable, it may cause data loss. This option is way faster than the second one, but it is not recommended to this method for long-term storage, because the source files may be unavailable in the future. The second option will download the image files to the dataset, it's safer but slower. You can choose the option that is more suitable for you.<br>
**Step 8:** The next option is to change the settings of the upload performance. It is disabled by default, which means that you don't need to change those settings in most cases. But if you want to change it, you can do it by unchecking the "Use default settings" checkbox and changing the values. The batch size value is the number of images to upload to the dataset in one batch. The second value is the number of workers to download images in parallel. Note that unoptimized settings may cause the app to work slower, so we recommend using the default settings unless you have a specific reason to change them.<br>
**Step 9:** In the "Destination" section, you can specify the project and the dataset to add the images. If you don't specify the project and the dataset, a new project and dataset will be created automatically using the search query and the current date for generating names. You can also specify the name of the project and the dataset manually if you want to create them with custom names. Note that if you are adding images to the existing dataset, where you have already downloaded some images for the same (or similar) search query, you should use the "Starting image number" from step 5 to skip the already downloaded images.
**Step 10:** After completing all the previous steps, you can click the "Start Upload" button to start downloading images from Flickr and uploading them to the dataset. The app will show you the progress of the upload, and you can also cancel the upload at any time by pressing the "Cancel upload" button.<br>

After the upload is finished, you will see a message with the number of images that have been successfully uploaded to the dataset. The app will also show the number of duplicates that were skipped during the upload and the number of images that were unavailable for download. 