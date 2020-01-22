# This script has been used to run ilastik locally and import the results to OMERO

import os
import numpy as np
import subprocess
from omero.gateway import BlitzGateway
from getpass import getpass

ILASTIK_PATH = '/home/julio/Apps/ilastik-1.3.2post1-Linux/run_ilastik.sh'
DIRECTORY = '/run/media/julio/DATA/Quentin/training_dataset/numpy_arrays'
DIRECTORY2 = '/media/sf_DATA/Quentin/training_dataset/numpy_arrays'
MODELS = ['Nuclei_model_v3.ilp', 'Ch1_model_v3.ilp', 'Ch2_model_v3.ilp', 'Ch2_model_v3.ilp']
INPUT_SUBFIXES = ['DAPI.npy', 'DAPI_Ch1.npy', 'DAPI_Ch2.npy', 'DAPI_Ch3.npy']

HOST = 'localhost'
PORT = 4064
USER = input('Username:')
PW = getpass()
DATASET_ID = 251
OUTPUT_SUBFIX = '_Probabilities.npy'


def plane_gen(data):
    """
    Set up a generator of 2D numpy arrays.

    The createImage method below expects planes in the order specified here
    (for z.. for c.. for t..)

    """
    for z in range(data.shape[0]):  # all Z sections data.shape[0]
        for c in range(data.shape[1]):  # all channels
            for t in range(data.shape[2]):  # all time-points
                yield data[z][c][t]


def run_ilastik(ilastik_path, directory, models, subfixes):
    files = os.listdir(directory)
    
    for m in range(len(models)):
        inputs = []
        for f in files:
            if subfixes[m] in f:
                inputs.append(os.path.join(directory, f))
        
        for i in inputs:
            cmd = [ilastik_path,
                   '--headless',
                   f'--project={os.path.join(directory, models[m])}',
                   '--export_source=Probabilities',
                   '--output_format=numpy',
                   # f'--output_filename_format={{dataset_dir}}/{{nickname}}_Probabilities.npy',
                   '--output_axis_order=zctxy',
                   i]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout
            except subprocess.CalledProcessError as e:
                print(f'Input command: {cmd}')
                print()
                print(f'Error: {e.output}')
                print()
                print(f'Command: {e.cmd}')
                print()


def import_np_arrays(host, port, user, pw, dataset_id, directory, subfix):
    conn = BlitzGateway(user, pw, host=host, port=port)
    conn.connect()
    dataset = conn.getObject('Dataset', dataset_id)
    print(f'Destination dataset is: {dataset.getname()}')

    files = os.listdir(directory)

    for file in files:
        if subfix in file:
            # Save the probabilities file
            omero_name = file
            print(f'Saving Probabilities as an Image in OMERO as {omero_name}')
            output_data = np.load(os.path.join(directory, file))
            print(f'old shape = {output_data.shape}')
            if len(output_data.shape) == 4:
                output_data = output_data.reshape(output_data.shape[:2] + (1,) + output_data.shape[2:])
            print(f'new shape = {output_data.shape}')
            desc = f'ilastik probabilities'
            conn.createImageFromNumpySeq(zctPlanes=plane_gen(output_data[1]),
                                         imageName=omero_name,
                                         sizeZ=output_data.shape[1],
                                         sizeC=output_data.shape[0],
                                         sizeT=output_data.shape[2],
                                         description=desc,
                                         dataset=dataset)

    conn.close()


if __name__ == '__main__':
    run_ilastik(ilastik_path=ILASTIK_PATH,
                directory=DIRECTORY2,
                models=MODELS,
                subfixes=INPUT_SUBFIXES,
                )

    import_np_arrays(host=HOST,
                     port=PORT,
                     user=USER,
                     pw=PW,
                     dataset_id=DATASET_ID,
                     directory=DIRECTORY,
                     subfix=OUTPUT_SUBFIX,
                     )

    print("done")
