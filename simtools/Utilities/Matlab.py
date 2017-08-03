import scipy.io


def read_mat_points_file(filename, header_key='jp', points_key='vals'):
    mat = scipy.io.loadmat(filename, squeeze_me=True, struct_as_record=False)
    points = mat[points_key]
    header = mat[header_key][0]
    return header.tolist(), points.tolist()
