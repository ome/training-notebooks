# training-notebooks

A set of Notebooks to demonstrate how to access the images and metadata from OMERO.

To build the image run, in this repository:

    $ docker build -t training-notebooks .

The image contains the dependencies required to connect to OMERO 5.4.x.

To start the image:

    $ docker run -it  -p 8888:8888 training-notebooks

The notebooks in this repository are meant to exemplify how to access data in OMERO.

| **Notebook** | **Lang** | **Description** |
|--------------|----------|-----------------|
| **[OMERO example](Python/OMEROHelloWorldNotebook.ipynb)** | Py | Shows how to connect to OMERO and read data. |
| **[Calculate Sharpness](Python/CalculateSharpness.ipynb)** | Py | Calculates sharpness of images and generates heatmaps. |
| **[Illumination Correction](Python/IlluminationCorrectionNotebook.ipynb)** | Py | Correct the selected image. |
