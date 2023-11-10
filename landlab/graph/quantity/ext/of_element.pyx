import multiprocessing

cimport cython
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from cython.parallel import prange
from cython cimport view


ctypedef fused element_id_type:
    cython.integral


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef diff_children_at_parent(
    const element_id_type [:, :] children_at_parent,
    const cython.floating [:] value_at_parent,
    const cython.floating [:] value_at_child,
    cython.floating [:, :] out,
):
    """Calculate differences between parents and children.

    Parameters
    ----------
    children_at_parent : array of shape (n_parents, max_children)
        Array that specifies the children of each parent as indices
        into the *value_at_child* array. Values of -1 indicate
        non-existant children.
    value_at_parent : array
        Value for each parent.
    value_at_child : array
        Value for each child.
    """
    cdef int n_parents = children_at_parent.shape[0]
    cdef int n_cols = children_at_parent.shape[1]
    cdef int parent, child
    cdef int col

    for parent in prange(n_parents, nogil=True, schedule="static"):
        for col in range(n_cols):
            child = children_at_parent[parent, col]
            if child >= 0:
                out[parent, col] = value_at_child[child] - value_at_parent[parent]


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef mean_of_children_at_parent(
    element_id_type [:, :] children_at_parent,
    cython.floating [:] value_at_child,
    cython.floating [:] out,
):
    """Calculate means of parents' children.

    Parameters
    ----------
    children_at_parent : array of shape (n_parents, max_children)
        Array that specifies the children of each parent as indices
        into the *value_at_child* array. Values of -1 indicate
        non-existant children.
    value_at_child : array
        Value for each child.
    """
    cdef int n_parents = children_at_parent.shape[0]
    cdef int n_cols = children_at_parent.shape[1]
    cdef int parent, col
    cdef int child
    cdef int count
    cdef cython.floating total

    for parent in prange(n_parents, nogil=True, schedule="static"):
        count = 0
        total = 0
        for col in range(n_cols):
            child = children_at_parent[parent, col]
            if child >= 0:
                total = total + value_at_child[child]
                count = count + 1
        if count > 0:
            out[parent] = total / count


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef min_of_children_at_parent(
    element_id_type [:, :] children_at_parent,
    cython.floating [:] value_at_child,
    cython.floating [:] out,
):
    """Calculate minimums of parents' children.

    Parameters
    ----------
    children_at_parent : array of shape (n_parents, max_children)
        Array that specifies the children of each parent as indices
        into the *value_at_child* array. Values of -1 indicate
        non-existant children.
    value_at_child : array
        Value for each child.
    """
    cdef int n_parents = children_at_parent.shape[0]
    cdef int n_cols = children_at_parent.shape[1]
    cdef int parent, col
    cdef int child
    cdef cython.floating value, min_value
    cdef int first

    for parent in prange(n_parents, nogil=True, schedule="static"):
        first = n_cols
        for col in range(n_cols):
            child = children_at_parent[parent, col]
            if child != -1:
                first = col
                min_value = value_at_child[child]
                break
        for col in range(first + 1, n_cols):
            child = children_at_parent[parent, col]
            if child != -1:
                value = value_at_child[child]
                if value < min_value:
                    min_value = value
        if first < n_cols:
            out[parent] = min_value


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef max_of_children_at_parent(
    element_id_type [:, :] children_at_parent,
    cython.floating [:] value_at_child,
    cython.floating [:] out,
):
    """Calculate maximums of parents' children.

    Parameters
    ----------
    children_at_parent : array of shape (n_parents, max_children)
        Array that specifies the children of each parent as indices
        into the *value_at_child* array. Values of -1 indicate
        non-existant children.
    value_at_child : array
        Value for each child.
    """
    cdef int n_parents = children_at_parent.shape[0]
    cdef int n_cols = children_at_parent.shape[1]
    cdef int parent, col
    cdef int child
    cdef cython.floating value, max_value
    cdef int first

    for parent in prange(n_parents, nogil=True, schedule="static"):
        first = n_cols
        for col in range(n_cols):
            child = children_at_parent[parent, col]
            if child != -1:
                first = col
                max_value = value_at_child[child]
                break
        for col in range(first + 1, n_cols):
            child = children_at_parent[parent, col]
            if child != -1:
                value = value_at_child[child]
                if value > max_value:
                    max_value = value
        if first < n_cols:
            out[parent] = max_value


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef count_of_children_at_parent(
    const element_id_type [:, :] children_at_parent,
    # const cython.integral[:, :] children_at_parent,
    cython.integral [:] out,
):
    """Count the number of children for each parent.

    Parameters
    ----------
    children_at_parent : array of shape (n_parents, max_children)
        Array that specifies the children of each parent as indices
        into the *value_at_child* array. Values of -1 indicate
        non-existant children.
    """
    cdef int n_parents = children_at_parent.shape[0]
    cdef int n_cols = children_at_parent.shape[1]
    cdef int parent, col
    cdef int count
    # cdef char [:, :] is_valid = view.array(shape=(n_rows, n_cols), itemsize=sizeof(char), format="c", allocate_buffer=True)

    # for row in prange(n_rows, nogil=True, schedule="static"):
    #     for col in range(n_cols):
    #         # is_valid[row, col] = elements_at_element[row, col] != -1
    #         if elements_at_element[row, col] == -1:
    #             is_valid[row, col] = 0
    #         else:
    #             is_valid[row, col] = 1

    # for row in prange(n_rows, nogil=True, schedule="static"):
    #     # out[row] = 0
    #     count = 0
    #     for col in range(n_cols):
    #         if is_valid[row, col]:
    #             count = count + 1
    #             # out[row] = out[row] + 1
    #     out[row] = count
    for parent in prange(n_parents, nogil=True, schedule="static"):
        count = 0
        for col in range(n_cols):
            if children_at_parent[parent, col] != -1:
                count = count + 1
        out[parent] = count
