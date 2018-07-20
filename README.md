# training-notebooks

A set of Notebooks to demonstrate how to access the images and metadata from OMERO.

To build the image run, in this repository:

    $ docker build -t training-notebooks .

The image contains the dependencies required to connect to OMERO 5.4.x.

To start the image:

    $ docker run -it  -p 8888:8888 training-notebooks

To update a notebook while this is running:
In another terminal, get the container ID and copy a notebook e.g. idr0002.ipynb

	$ docker ps
	$ docker cp CellProfiler/idr0002.ipynb <container_id>:/home/jovyan/notebooks/CellProfiler/idr0002.ipynb

Now refresh the notebook in the browser.

To restart a container and get the URL to open in your browser:

	$ docker restart <container_id>
	$ docker logs <container_id>


The notebooks in this repository are meant to exemplify how to access data in OMERO.

| **Notebook** | **Lang** | **Description** |
|--------------|----------|-----------------|
| **[OMERO example](Python/OMEROHelloWorldNotebook.ipynb)** | Py | Shows how to connect to OMERO and read data. |
| **[Calculate Sharpness](Python/CalculateSharpnessOneImage.ipynb)** | Py | Calculates sharpness of images and generates heatmaps. |
| **[Illumination Correction](Python/IlluminationCorrectionNotebook.ipynb)** | Py | Correct the selected image. |
| **[R-OMERO example](R/R-OMERO_Notebook.ipynb)** | R | Shows how to connect to OMERO and manipulate data using R. |
| **[idr0021 ROIs](R/idr0021_rois.ipynb)** | R | Read OMERO.table data, performs some basic statistics on it and create a plot. |
| **[Statistics Fruit Fly](CellProfiler/statistics_fruit_fly.ipynb)** | Py | Process Images stored in OMERO using CellProfiler. |
| **[idr0002](CellProfiler/idr0002.ipynb)** | Py | Process a plate from idr0002 using CellProfiler. |
