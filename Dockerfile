FROM manics/jupyter-docker:jupyter-0.8
MAINTAINER ome-devel@lists.openmicroscopy.org.uk

# create a python2 environment (for OMERO-PY compatibility)
ADD docker/environment-python2-omero.yml .setup/
RUN conda env update -n python2 -f .setup/environment-python2-omero.yml

RUN /opt/conda/envs/python2/bin/python -m ipykernel install --user --name python2 --display-name 'OMERO Python 2'
ADD docker/logo-32x32.png docker/logo-64x64.png .local/share/jupyter/kernels/python2/

RUN git clone -b master https://github.com/ome/training-notebooks.git notebooks
