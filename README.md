# training-notebooks

A set of Notebooks to demonstrate how to access the images and metadata from OMERO.

To build the image run, in this repository:

    $ docker build -t training-notebooks .

The image contains the dependencies required to connect to OMERO 5.5.x.

To start the image in Jupyter:

    $ docker run -it  -p 8888:8888 training-notebooks

To start the image in Jupyterlab:

    $ docker run -it  -p 8888:8888 -e JUPYTER_ENABLE_LAB=true training-notebooks

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
| **[SimpleFRAP](Python/SimpleFRAP.ipynb)** | Py | Process a dataset measuring the intensity in a named Channel within a ROI. |


The notebooks have now been copied to other repositories as specified below. The new repositories give the possiblity to run these notebooks using [BinderHub](https://binderhub.readthedocs.io/en/latest/). The notebooks in this repository which were copied will be deleted later:

* Notebooks under [CellProfiler](CellProfiler) are now available at [omero-guide-cellprofiler](https://github.com/ome/omero-guide-cellprofiler).
* Notebooks under [ilastik](ilastik) are now available at [omero-guide-ilastik](https://github.com/ome/omero-guide-ilastik).
* Notebooks under [Fiji](Fiji) are now available at [omero-guide-fiji](https://github.com/ome/omero-guide-fiji).
* Notebooks under [Orbit](Orbit) are now available at [omero-guide-orbit](https://github.com/ome/omero-guide-orbit).
* Notebooks under [Python](Python) are now available at [omero-guide-python](https://github.com/ome/omero-guide-python).
* Notebooks under [R](R) are now available at [omero-guide-r](https://github.com/ome/omero-guide-r).
