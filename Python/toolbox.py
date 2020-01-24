import omero.gateway as gw
from omero.constants import metadata, namespaces
from omero import model
from omero.model import enums, LengthI
from omero import grid
from omero import rtypes
from itertools import product
from json import dumps
from random import choice
from string import ascii_letters
from skimage.filters import threshold_otsu, apply_hysteresis_threshold, gaussian
from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.morphology import closing, cube
from skimage.feature import peak_local_max
from scipy.spatial.distance import cdist
import numpy as np
from itertools import permutations


COLUMN_TYPES = {'string': grid.StringColumn,
                'long': grid.LongColumn,
                'bool': grid.BoolColumn,
                'double': grid.DoubleColumn,
                'long_array': grid.LongArrayColumn,
                'float_array': grid.FloatArrayColumn,
                'double_array': grid.DoubleArrayColumn,
                'image': grid.ImageColumn,
                'dataset': grid.DatasetColumn,
                'plate': grid.PlateColumn,
                'well': grid.WellColumn,
                'roi': grid.RoiColumn,
                'mask': grid.MaskColumn,
                'file': grid.FileColumn,
                }


def open_connection(username, password, group, port, host, secure=False):
    conn = gw.BlitzGateway(username=username,
                           passwd=password,
                           group=group,
                           port=port,
                           host=host,
                           secure=secure)
    try:
        conn.connect()
    except Exception as e:
        raise e
    return conn


def close_connection(connection):
    connection.close()


def get_image(connection, image_id):
    try:
        image = connection.getObject('Image', image_id)
    except Exception as e:
        raise e
    return image


def get_dataset(connection, dataset_id):
    try:
        dataset = connection.getObject('Dataset', dataset_id)
    except Exception as e:
        raise e
    return dataset


def get_project(connection, project_id):
    try:
        project = connection.getObject('Project', project_id)
    except Exception as e:
        raise e
    return project


def get_image_shape(image):
    try:
        image_shape = (image.getSizeZ(),
                       image.getSizeC(),
                       image.getSizeT(),
                       image.getSizeX(),
                       image.getSizeY())
    except Exception as e:
        raise e

    return image_shape


def get_pixel_sizes(image):
    pixels = image.getPrimaryPixels()

    pixel_sizes = (pixels.getPhysicalSizeX().getValue(),
                   pixels.getPhysicalSizeY().getValue(),
                   pixels.getPhysicalSizeZ().getValue())
    return pixel_sizes


def get_pixel_units(image):
    pixels = image.getPrimaryPixels()

    pixel_size_units = (pixels.getPhysicalSizeX().getUnit().name,
                        pixels.getPhysicalSizeY().getUnit().name,
                        pixels.getPhysicalSizeZ().getUnit().name)
    return pixel_size_units


def get_intensities(image, z_range=None, c_range=None, t_range=None, x_range=None, y_range=None):
    """Returns a numpy array containing the intensity values of the image
    Returns an array with dimensions arranged as zctxy
    """
    image_shape = get_image_shape(image)

    # Decide if we are going to call getPlanes or getTiles
    if not x_range and not y_range:
        whole_planes = True
    else:
        whole_planes = False

    ranges = list(range(5))
    for dim, r in enumerate([z_range, c_range, t_range, x_range, y_range]):
        # Verify that requested ranges are within the available data
        if r is None:  # Range is not specified
            ranges[dim] = range(image_shape[dim])
        else:  # Range is specified
            if type(r) is int:
                ranges[dim] = range(r, r + 1)
            elif type(r) is not tuple:
                raise TypeError('Range is not provided as a tuple.')
            else:  # range is a tuple
                if len(r) == 1:
                    ranges[dim] = range(r[0])
                elif len(r) == 2:
                    ranges[dim] = range(r[0], r[1])
                elif len(r) == 3:
                    ranges[dim] = range(r[0], r[1], r[2])
                else:
                    raise IndexError('Range values must contain 1 to three values')
            if not 1 <= ranges[dim].stop <= image_shape[dim]:
                raise IndexError('Specified range is outside of the image dimensions')

    output_shape = (len(ranges[0]), len(ranges[1]), len(ranges[2]), len(ranges[3]), len(ranges[4]))
    nr_planes = output_shape[0] * output_shape[1] * output_shape[2]
    zct_list = list(product(ranges[0], ranges[1], ranges[2]))

    pixels = image.getPrimaryPixels()
    pixels_type = pixels.getPixelsType()
    if pixels_type.value == 'float':
        data_type = pixels_type.value + str(pixels_type.bitSize)  # TODO: Verify this is working for all data types
    else:
        data_type = pixels_type.value

    intensities = np.zeros((nr_planes,
                            output_shape[3],
                            output_shape[4]),
                           dtype=data_type)
    if whole_planes:
        np.stack(list(pixels.getPlanes(zctList=zct_list)), out=intensities)
    else:
        tile_region = (ranges[3].start, ranges[4].start, len(ranges[3]), len(ranges[4]))
        zct_tile_list = [(z, c, t, tile_region) for z, c, t in zct_list]
        np.stack(list(pixels.getTiles(zctTileList=zct_tile_list)), out=intensities)

    intensities = np.reshape(intensities, newshape=output_shape)

    return intensities


############### Creating projects and datasets #####################

def create_project(connection, project_name):
    new_project = gw.ProjectWrapper(connection)
    new_project.setName(rtypes.rstring(project_name))
    new_project.save()

    return new_project


def create_dataset(connection, dataset_name, dataset_description=None, parent_project=None):
    new_dataset = model.DatasetI()
    new_dataset.setName(rtypes.rstring(dataset_name))
    if dataset_description:
        new_dataset.setDescription(rtypes.rstring(dataset_description))
    new_dataset = connection.getUpdateService().saveAndReturnObject(new_dataset)
    if parent_project:
        link = model.ProjectDatasetLinkI()
        link.setParent(parent_project._obj)
        link.setChild(new_dataset)
        connection.getUpdateService().saveObject(link)

    return new_dataset


############### Getting information on projects and datasets ###############

def get_project_datasets(project):
    datasets = project.listChildren()

    return datasets


def get_dataset_images(dataset):
    images = dataset.listChildren()

    return images


# In this section we give some convenience functions to send data back to OMERO #

def create_annotation_tag(connection, tag_string):
    tag_ann = gw.TagAnnotationWrapper(connection)
    tag_ann.setValue(tag_string)
    tag_ann.save()

    return tag_ann


def _serialize_map_value(value):
    if isinstance(value, str):
        return value
    else:
        try:
            return dumps(value)
        except ValueError as e:
            # TODO: log an error
            return dumps(value.__str__())


def _dict_to_map(dictionary):
    """Converts a dictionary into a list of key:value pairs to be fed as map annotation.
    If value is not a string we serialize it as a json string"""
    map_annotation = [[k, _serialize_map_value(v)] for k, v in dictionary.items()]
    return map_annotation


def create_annotation_map(connection, annotation, client_editable=True):
    """Creates a map_annotation for OMERO. It can create a map annotation from a
    dictionary or from a list of 2 elements list.
    """
    # Convert a dictionary into a map annotation
    if isinstance(annotation, dict):
        annotation = _dict_to_map(annotation)
    elif isinstance(annotation, list):
        pass  # TODO: assert that the list is compliant with the OMERO format
    else:
        raise Exception(f'Could not convert {annotation} to a map_annotation')

    map_ann = gw.MapAnnotationWrapper(connection)

    if client_editable:
        namespace = metadata.NSCLIENTMAPANNOTATION  # This makes the annotation editable in the client
        map_ann.setNs(namespace)

    map_ann.setValue(annotation)
    map_ann.save()

    return map_ann


def create_annotation_file_local(connection, file_path, namespace=None, description=None):
    """Creates a file annotation and uploads it to OMERO"""

    file_ann = connection.createFileAnnfromLocalFile(localPath=file_path,
                                                     mimetype=None,
                                                     namespace=namespace,
                                                     desc=description)
    return file_ann


def _create_column(data_type, kwargs):
    column_class = COLUMN_TYPES[data_type]

    return column_class(**kwargs)


def _create_table(column_names, columns_descriptions, values):
    columns = list()
    for cn, cd, v in zip(column_names, columns_descriptions, values):
        if isinstance(v[0], str):
            size = len(max(v, key=len))
            args = {'name': cn, 'description': cd, 'size': size, 'values': v}
            columns.append(_create_column(data_type='string', kwargs=args))
        elif isinstance(v[0], int):
            args = {'name': cn, 'description': cd, 'values': v}
            columns.append(_create_column(data_type='long', kwargs=args))
        elif isinstance(v[0], float):
            args = {'name': cn, 'description': cd, 'values': v}
            columns.append(_create_column(data_type='double', kwargs=args))
        elif isinstance(v[0], bool):
            args = {'name': cn, 'description': cd, 'values': v}
            columns.append(_create_column(data_type='string', kwargs=args))
        else:
            raise Exception(f'Could not detect column datatype for {v[0]}')

    return columns


def create_annotation_table(connection, table_name, column_names, column_descriptions, values, namespace=None, description=None):
    """Creates a table annotation from a list of lists"""

    table_name = f'{table_name}_{"".join([choice(ascii_letters) for n in range(32)])}.h5'

    columns = _create_table(column_names=column_names,
                            columns_descriptions=column_descriptions,
                            values=values)
    resources = connection.c.sf.sharedResources()
    repository_id = resources.repositories().descriptions[0].getId().getValue()
    table = resources.newTable(repository_id, table_name)
    table.initialize(columns)
    table.addData(columns)

    original_file = table.getOriginalFile()
    table.close()  # when we are done, close.
    file_ann = gw.FileAnnotationWrapper(connection)
    file_ann.setNs(namespaces.NSBULKANNOTATIONS)
    file_ann.setFile(model.OriginalFileI(original_file.id.val, False))  # TODO: try to get this with a wrapper
    file_ann.save()
    return file_ann


def create_roi(connection, image, shapes):
    """A pass through to create a roi into an image"""
    return _create_roi(connection, image, shapes)


def _create_roi(connection, image, shapes):
    # create an ROI, link it to Image
    roi = model.RoiI()
    # use the omero.model.ImageI that underlies the 'image' wrapper
    roi.setImage(image._obj)
    for shape in shapes:
        roi.addShape(shape)
    # Save the ROI (saves any linked shapes too)
    return connection.getUpdateService().saveAndReturnObject(roi)


def _rgba_to_int(red, green, blue, alpha=255):
    """ Return the color as an Integer in RGBA encoding """
    r = red << 24
    g = green << 16
    b = blue << 8
    a = alpha
    rgba_int = sum([r, g, b, a])
    if rgba_int > (2**31-1):       # convert to signed 32-bit int
        rgba_int = rgba_int - 2**32

    return rgba_int


def _set_shape_properties(shape, name=None,
                          fill_color=(10, 10, 10, 255),
                          stroke_color=(255, 255, 255, 255),
                          stroke_width=1, ):
    if name:
        shape.setTextValue(rtypes.rstring(name))
    shape.setFillColor(rtypes.rint(_rgba_to_int(*fill_color)))
    shape.setStrokeColor(rtypes.rint(_rgba_to_int(*stroke_color)))
    shape.setStrokeWidth(LengthI(stroke_width, enums.UnitsLength.PIXEL))


def create_shape_point(x_pos, y_pos, z_pos, t_pos, point_name=None):
    point = model.PointI()
    point.x = rtypes.rdouble(x_pos)
    point.y = rtypes.rdouble(y_pos)
    point.theZ = rtypes.rint(z_pos)
    point.theT = rtypes.rint(t_pos)
    _set_shape_properties(point, name=point_name)

    return point


def create_shape_line(x1_pos, y1_pos, x2_pos, y2_pos, z_pos, t_pos,
                      line_name=None, stroke_color=(255, 255, 255, 255), stroke_width=1):
    line = model.LineI()
    line.x1 = rtypes.rdouble(x1_pos)
    line.x2 = rtypes.rdouble(x2_pos)
    line.y1 = rtypes.rdouble(y1_pos)
    line.y2 = rtypes.rdouble(y2_pos)
    line.theZ = rtypes.rint(z_pos)
    line.theT = rtypes.rint(t_pos)
    _set_shape_properties(line, name=line_name,
                          stroke_color=stroke_color,
                          stroke_width=stroke_width)
    return line


def create_shape_rectangle(x_pos, y_pos, width, height, z_pos, t_pos,
                           rectangle_name=None,
                           fill_color=(10, 10, 10, 255),
                           stroke_color=(255, 255, 255, 255),
                           stroke_width=1):
    rect = model.RectangleI()
    rect.x = rtypes.rdouble(x_pos)
    rect.y = rtypes.rdouble(y_pos)
    rect.width = rtypes.rdouble(width)
    rect.height = rtypes.rdouble(height)
    rect.theZ = rtypes.rint(z_pos)
    rect.theT = rtypes.rint(t_pos)
    _set_shape_properties(shape=rect, name=rectangle_name,
                          fill_color=fill_color,
                          stroke_color=stroke_color,
                          stroke_width=stroke_width)
    return rect


def create_shape_ellipse(x_pos, y_pos, x_radius, y_radius, z_pos, t_pos,
                         ellipse_name=None,
                         fill_color=(10, 10, 10, 255),
                         stroke_color=(255, 255, 255, 255),
                         stroke_width=1):
    ellipse = model.EllipseI()
    ellipse.setX(rtypes.rdouble(x_pos))
    ellipse.setY(rtypes.rdouble(y_pos))  # TODO: setters and getters everywhere
    ellipse.radiusX = rtypes.rdouble(x_radius)
    ellipse.radiusY = rtypes.rdouble(y_radius)
    ellipse.theZ = rtypes.rint(z_pos)
    ellipse.theT = rtypes.rint(t_pos)
    _set_shape_properties(ellipse, name=ellipse_name,
                          fill_color=fill_color,
                          stroke_color=stroke_color,
                          stroke_width=stroke_width)
    return ellipse


def create_shape_polygon(points_list, z_pos, t_pos,
                         polygon_name=None,
                         fill_color=(10, 10, 10, 255),
                         stroke_color=(255, 255, 255, 255),
                         stroke_width=1):
    polygon = model.PolygonI()
    points_str = "".join(["".join([str(x), ',', str(y), ', ']) for x, y in points_list])[:-2]
    polygon.points = rtypes.rstring(points_str)
    polygon.theZ = rtypes.rint(z_pos)
    polygon.theT = rtypes.rint(t_pos)
    _set_shape_properties(polygon, name=polygon_name,
                          fill_color=fill_color,
                          stroke_color=stroke_color,
                          stroke_width=stroke_width)
    return polygon


def create_shape_mask(mask_array, x_pos, y_pos, z_pos, t_pos,
                      mask_name=None,
                      fill_color=(10, 10, 10, 255)):
    mask = model.MaskI()
    mask.setX(rtypes.rdouble(x_pos))
    mask.setY(rtypes.rdouble(y_pos))
    mask.setTheZ(rtypes.rint(z_pos))
    mask.setTheT(rtypes.rint(t_pos))
    mask.setWidth(rtypes.rdouble(mask_array.shape[0]))
    mask.setHeight(rtypes.rdouble(mask_array.shape[1]))
    mask.setFillColor(rtypes.rint(_rgba_to_int(*fill_color)))
    if mask_name:
        mask.setTextValue(rtypes.rstring(mask_name))
    mask_packed = np.packbits(mask_array)  # TODO: raise error when not boolean array
    mask.setBytes(mask_packed.tobytes())

    return mask


def link_annotation(object_wrapper, annotation_wrapper):
    object_wrapper.linkAnnotation(annotation_wrapper)


###### Image analysis functions #######

def segment_channel(channel, min_distance, sigma, method, hysteresis_levels):
    """Segment a channel (3D numpy array)"""
    threshold = threshold_otsu(channel)

    # TODO: Threshold be a sigma passed here
    if sigma:
        gauss_filtered = gaussian(image=channel,
                                  multichannel=False,
                                  sigma=sigma,
                                  preserve_range=True)
    else:
        gauss_filtered = channel

    if method == 'hysteresis':  # We may try here hysteresis threshold
        thresholded = apply_hysteresis_threshold(gauss_filtered,
                                                 low=hysteresis_levels[0],
                                                 high=hysteresis_levels[1]
                                                 )

    elif method == 'local_max':  # We are applying a local maxima algorithm
        peaks = peak_local_max(gauss_filtered,
                               min_distance=min_distance,
                               threshold_abs=(threshold * .5),
                               exclude_border=True,
                               indices=False
                               )
        thresholded = np.copy(gauss_filtered)
        thresholded[peaks] = thresholded.max()
        thresholded = apply_hysteresis_threshold(thresholded,
                                                 low=threshold * hysteresis_levels[0],
                                                 high=threshold * hysteresis_levels[1]
                                                 )
    else:
        raise Exception('A valid segmentation method was not provided')

    closed = closing(thresholded, cube(min_distance))
    cleared = clear_border(closed)
    return label(cleared)


def compute_channel_spots_properties(channel, label_channel, pixel_size=None):
    """Analyzes and extracts the properties of a single channel"""

    ch_properties = list()

    regions = regionprops(label_channel, channel)

    for region in regions:
        ch_properties.append({'label': region.label,
                              'area': region.area,
                              # XY coordinates are swapped in a numpy array compared to an image
                              'centroid': (region.centroid[0], region.centroid[1], region.centroid[1]),
                              'weighted_centroid': (region.weighted_centroid[0], region.weighted_centroid[2], region.weighted_centroid[1]),
                              'max_intensity': region.max_intensity,
                              'mean_intensity': region.mean_intensity,
                              'min_intensity': region.min_intensity
                              })

    return ch_properties


def compute_distances_matrix(positions, sigma, pixel_size=None, remove_mcn=False):
    """Calculates Mutual Closest Neighbour distances between all channels and returns the values as
    a list of tuples where the first element is a tuple with the channel combination (ch_A, ch_B) and the second is
    a list of pairwise measurements where, for every spot s in ch_A:
    - Positions of s (s_x, s_y, s_z)
    - Weighted euclidean distance dst to the nearest spot in ch_B, t
    - Index t_index of the nearest spot in ch_B
    Like so:
    [((ch_A, ch_B), [[(s_x, s_y, s_z), dst, t_index],...]),...]
    """
    # TODO: Correct documentation
    # Container for results
    distances = list()

    if len(positions) < 2:
        raise Exception('Not enough dimensions to do a distance measurement')

    channel_permutations = list(permutations(range(len(positions)), 2))

    # Create a space to hold the distances. For every channel permutation (a, b) we want to store:
    # Coordinates of a
    # Distance to the closest spot in b
    # Index of the nearest spot in b

    if not pixel_size:
        pixel_size = np.array((1, 1, 1))
        # TODO: log warning
    else:
        pixel_size = np.array(pixel_size)

    for a, b in channel_permutations:
        # TODO: Try this
        # TODO: Make explicit arguments of cdist
        distances_matrix = cdist(positions[a], positions[b], w=pixel_size)

        pairwise_distances = {'channels': (a, b),
                              'coord_A': list(),
                              'dist_3d': list(),
                              'index_A': list(),
                              'index_B': list()
                              }
        for index_a, (p, d) in enumerate(zip(positions[a], distances_matrix)):
            if d.min() < sigma:
                # We remove the mutual closest neighbours
                if remove_mcn and distances_matrix[:, d.argmin()].argmin() != index_a:
                    continue
                else:
                    pairwise_distances['coord_A'].append(tuple(p))
                    pairwise_distances['dist_3d'].append(d.min())
                    pairwise_distances['index_A'].append(index_a)
                    pairwise_distances['index_B'].append(d.argmin())

        distances.append(pairwise_distances)

    return distances
