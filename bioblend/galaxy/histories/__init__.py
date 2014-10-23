"""
Contains possible interactions with the Galaxy Histories
"""
import bioblend
from bioblend.galaxy.client import Client

import os
import re
import shutil
import shlex
import urlparse
import urllib2
import time


class HistoryClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'histories'
        super(HistoryClient, self).__init__(galaxy_instance)

    def create_history(self, name=None):
        """
        Create a new history, optionally setting the ``name``.
        """
        payload = {}
        if name is not None:
            payload['name'] = name
        return Client._post(self, payload)

    def get_histories(self, history_id=None, name=None, deleted=False):
        """
        Get all histories or filter the specific one(s) via the provided ``name``
        or ``history_id``. Provide only one argument, ``name`` or ``history_id``,
        but not both.

        If ``deleted`` is set to ``True``, return histories that have been deleted.

        Return a list of history element dicts. If more than one history
        matches the given ``name``, return the list of all the histories with the
        given name.
        """
        if history_id is not None and name is not None:
            raise ValueError('Provide only one argument between name or history_id, but not both')
        histories = Client._get(self, deleted=deleted)
        if history_id is not None:
            history = next((_ for _ in histories if _['id'] == history_id), None)
            histories = [history] if history is not None else []
        elif name is not None:
            histories = [_ for _ in histories if _['name'] == name]
        return histories

    def show_history(self, history_id, contents=False, deleted=None, visible=None, details=None, types=None):
        """
        Get details of a given history. By default, just get the history meta
        information. If ``contents`` is set to ``True``, get the complete list of
        datasets in the given history. ``deleted``, ``visible``, and ``details`` are
        used only if ``contents`` is ``True`` and are used to modify the datasets returned
        and their contents. Set ``details`` to 'all' to get more information
        about each dataset.
        """
        params = {}
        if contents:
            if details:
                params['details'] = details
            if deleted is not None:
                params['deleted'] = deleted
            if visible is not None:
                params['visible'] = visible
            if types is not None:
                params['types'] = types.join(",")
        return Client._get(self, id=history_id, contents=contents, params=params)

    def delete_dataset(self, history_id, dataset_id):
        """
        Mark corresponding dataset as deleted.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        Client._delete(self, payload={}, url=url)

    def delete_dataset_collection(self, history_id, dataset_collection_id):
        """
        Mark corresponding dataset collection as deleted.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        Client._delete(self, payload={}, url=url)

    def show_dataset(self, history_id, dataset_id):
        """
        Get details about a given history dataset. The required ``history_id``
        can be obtained from the datasets's history content details.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return Client._get(self, url=url)

    def show_dataset_collection(self, history_id, dataset_collection_id):
        """
        Get details about a given history dataset collection.
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        return Client._get(self, url=url)

    def show_matching_datasets(self, history_id, name_filter=None):
        """
        Get dataset details for matching datasets within a history.

        Only datasets whose name matches the ``name_filter`` regular
        expression will be returned; use plain strings for exact
        matches and None to match all datasets in the history.
        """
        if isinstance(name_filter, basestring):
            name_filter = re.compile(name_filter + '$')
        return [self.show_dataset(history_id, h['id'])
                for h in self.show_history(history_id, contents=True)
                if name_filter is None or name_filter.match(h['name'])]

    def show_dataset_provenance(self, history_id, dataset_id, follow=False):
        """
        Get details related to how dataset was created (``id``, ``job_id``,
        ``tool_id``, ``stdout``, ``stderr``, ``parameters``, ``inputs``,
        etc...).

        If ``follow`` is ``True``, recursively fetch dataset provenance
        information for all inputs and their inputs, etc....
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, dataset_id, "provenance"])
        return Client._get(self, url=url)

    def update_history(self, history_id, name=None, annotation=None, **kwds):
        """
        Update history metadata information. Some of the attributes that can be
        modified are documented below.

        :type history_id: string
        :param history_id: Encoded history ID
        :type name: string
        :param name: Replace history name with the given string
        :type annotation: string
        :param annotation: Replace history annotation with given string
        :type deleted: boolean
        :param deleted: Mark or unmark history as deleted
        :type published: boolean
        :param published: Mark or unmark history as published
        :type importable: boolean
        :param importable: Mark or unmark history as importable
        :type tags: list
        :param tags: Replace history tags with the given list

        :rtype: status_code (int)

        """
        kwds['name'] = name
        kwds['annotation'] = annotation
        return Client._put(self, kwds, id=history_id).status_code

    def update_dataset(self, history_id, dataset_id, **kwds):
        """
        Update history dataset metadata. Some of the attributes that can be
        modified are documented below.

        :type history_id: string
        :param history_id: Encoded history ID
        :type name: string
        :param name: Replace history dataset name with the given string
        :type annotation: string
        :param annotation: Replace history dataset annotation with given string
        :type deleted: boolean
        :param deleted: Mark or unmark history dataset as deleted
        :type visible: boolean
        :param visible: Mark or unmark history dataset as visible

        :rtype: status_code (int)
        """
        url = self.gi._make_url(self, history_id, contents=True)
        # Append the dataset_id to the base history contents URL
        url = '/'.join([url, dataset_id])
        return Client._put(self, payload=kwds, url=url).status_code

    def update_dataset_collection(self, history_id, dataset_collection_id, **kwds):
        """
        Update history dataset collection metadata. Some of the attributes that
        can be modified are documented below.

        :type history_id: string
        :param history_id: Encoded history ID
        :type name: string
        :param name: Replace history dataset collection name with the given string
        :type deleted: boolean
        :param deleted: Mark or unmark history dataset collection as deleted.
        :type visible: boolean
        :param visible: Mark or unmark history dataset collection as visible.

        :rtype: status_code (int)
        """
        url = self.gi._make_url(self, history_id, contents=True)
        url = '/'.join([url, "dataset_collections", dataset_collection_id])
        return Client._put(self, payload=kwds, url=url).status_code

    def create_history_tag(self, history_id, tag):
        """
        Create history tag

        :type history_id: string
        :param history_id: Encoded history ID
        :type tag: string
        :param tag: Add tag to history

        :rtype: json object
        :return: Return json object
                 For example::

                 {'model_class':'HistoryTagAssociation', 'user_tname': 'NGS_PE_RUN', 'id': 'f792763bee8d277a', 'user_value': None}

        """

        # empty payload since we are adding the new tag using the url
        payload = {}

        # creating the url
        url = self.url
        url = '/'.join([url, history_id, 'tags', tag])

        return Client._post(self, payload, url=url)

    def upload_dataset_from_library(self, history_id, lib_dataset_id):
        """
        Upload a dataset into the history from a library. Requires the
        library dataset ID, which can be obtained from the library
        contents.
        """
        payload = {
            'content': lib_dataset_id,
            'source': 'library',
            'from_ld_id': lib_dataset_id,  # compatibility with old API
        }
        return Client._post(self, payload, id=history_id, contents=True)

    def create_dataset_collection(self, history_id, collection_description):
        try:
            collection_description = collection_description.to_dict()
        except AttributeError:
            pass
        payload = dict(
            name=collection_description["name"],
            type="dataset_collection",
            collection_type=collection_description["collection_type"],
            element_identifiers=collection_description["element_identifiers"],
        )
        return Client._post(self, payload, id=history_id, contents=True)

    def download_dataset(self, history_id, dataset_id, file_path=None, use_default_filename=True,
                         wait_for_completion=False, maxwait=12000, chunk_size=1024, hda_ldda='hda'):
        """
        Downloads the dataset identified by 'id'.
        
        :type history_id: string
        :param history_id: Encoded history ID

        :type dataset_id: string
        :param dataset_id: Encoded Dataset ID

        :type file_path: string
        :param file_path: If the file_path argument is provided, the dataset will be streamed to disk
                          at that path (Should not contain filename if use_default_name=True).
                          If the file_path argument is not provided, a generator is created. This avoids reading 
                          the content at once into memory for large responses.

        :type use_default_filename: boolean
        :param use_default_filename: If the use_default_filename parameter is True, the exported
                                 file will be saved as file_path/%s,
                                 where %s is the dataset name.
                                 If use_default_name is False, file_path is assumed to
                                 contain the full file path including filename.

        :type wait_for_completion: boolean
        :param wait_for_completion: If wait_for_completion is True, this call will block until the dataset is ready.
                                    If the dataset state becomes invalid, a DatasetStateException will be thrown.
        
        :type chunk_size: int
        :param chunk_size: The chunk size is the number of bytes (1024 - the default) it should read into memory.

        :type maxwait: float
        :param maxwait: Time (in seconds) to wait for dataset to complete.
                        If the dataset state is not complete within this time, a DatasetTimeoutException will be thrown.
                        
        :type hda_ldda: string
        :param hda_ldda: Whether to show a history dataset ('hda' - the default) or library
                         dataset ('ldda').

        """
        if wait_for_completion:
            self._block_until_dataset_ready(dataset_id, maxwait=maxwait)
        
        dataset = self.show_dataset(history_id, dataset_id)
        if not dataset['state'] == 'ok':
            raise DatasetStateException("Dataset not ready. Dataset id: %s, current state: %s" % (dataset_id, dataset['state']))
               
        params = dict(
        hda_ldda=hda_ldda,
        )
               
        try:
            url = urlparse.urljoin(self.gi.base_url, dataset['download_url'])
        except KeyError:
            raise KeyError('download_url not found : Impossible to download this file')

        try:
            url = url + '?to_ext=%s' % dataset['file_ext']
        except KeyError:
            pass

        r = Client._raw_get(self, url=url)
        if file_path is None:
            return r.iter_content(chunk_size)
        else:
            if use_default_filename:
                try:
                    # First try to get the filename from the response headers
                    # We expect tokens 'filename' '=' to be followed by the quoted filename
                    tokens = [x for x in shlex.shlex(r.headers['content-disposition'], posix=True)]
                    header_filepath = tokens[tokens.index('filename') + 2]
                    filename = os.path.basename(header_filepath)
                except (ValueError, IndexError):
                    # If the filename was not in the header, build a useable filename ourselves.
                    try:
                        filename = dataset['name'] + '.' + dataset['file_ext']
                    except KeyError:
                        filename = dataset['name']
                file_local_path = os.path.join(file_path, filename)
            else:
                file_local_path = file_path

            with open(file_local_path, 'wb') as fp:
                for chunk in r.iter_content(chunk_size):
                    if not chunk:
                        break
                        
                    fp.write(chunk)

    def delete_history(self, history_id, purge=False):
        """
        Delete a history.

        If ``purge`` is set to ``True``, also purge the history. Note that for
        the purge option to work, ``allow_user_dataset_purge`` option must be
        set in the Galaxy's configuration file ``universe_wsgi.ini``
        """
        payload = {}
        if purge is True:
            payload['purge'] = purge
        return Client._delete(self, payload, id=history_id)

    def undelete_history(self, history_id):
        """
        Undelete a history
        """
        url = self.gi._make_url(self, history_id, deleted=True)
        # Append the 'undelete' action to the history URL
        url = '/'.join([url, 'undelete'])
        return Client._post(self, payload={}, url=url)

    def get_status(self, history_id):
        """
        Returns the state of this history as a dictionary, with the following keys.
        'state' = This is the current state of the history, such as ok, error, new etc.
        'state_details' = Contains individual statistics for various dataset states.
        'percent_complete' = The overall number of datasets processed to completion.
        """
        state = {}
        history = self.show_history(history_id)
        state['state'] = history['state']
        if history.get('state_details') is not None:
            state['state_details'] = history['state_details']
            total_complete = sum(history['state_details'].itervalues())
            if total_complete > 0:
                state['percent_complete'] = 100 * history['state_details']['ok'] / total_complete
            else:
                state['percent_complete'] = 0
        return state

    def get_current_history(self):
        """
        Deprecated method.

        Just an alias for get_most_recently_used_history().
        """
        return self.get_most_recently_used_history()

    def get_most_recently_used_history(self):
        """
        Returns the current user's most recently used history (not deleted).
        """
        url = self.gi._make_url(self, None)
        url = '/'.join([url, 'most_recently_used'])
        return Client._get(self, url=url)

    def export_history(self, history_id, gzip=True, include_hidden=False,
                       include_deleted=False, wait=False):
        """
        Start a job to create an export archive for the given history.

        :type history_id: str
        :param history_id: history ID

        :type gzip: bool
        :param gzip: create .tar.gz archive if :obj:`True`, else .tar

        :type include_hidden: bool
        :param include_hidden: whether to include hidden datasets
          in the export

        :type include_deleted: bool
        :param include_deleted: whether to include deleted datasets
          in the export

        :type wait: bool
        :param wait: if :obj:`True`, block until the export is ready;
          else, return immediately

        :rtype: str
        :return: ``jeha_id`` of the export, or empty if ``wait`` is
          :obj:`False` and the export is not ready.
        """
        params = {
            'gzip': gzip,
            'include_hidden': include_hidden,
            'include_deleted': include_deleted,
            }
        url = '%s/exports' % self.gi._make_url(self, history_id)
        while True:
            r = Client._put(self, {}, url=url, params=params)
            if not wait or r.status_code == 200:
                break
            time.sleep(1)
        contents = r.json()
        if contents:
            jeha_id = contents['download_url'].rsplit('/', 1)[-1]
        else:
            jeha_id = ''  # export is not ready
        return jeha_id

    def download_history(self, history_id, jeha_id, outf,
                         chunk_size=bioblend.CHUNK_SIZE):
        """
        Download a history export archive.  Use :meth:`export_history`
        to create an export.

        :type history_id: str
        :param history_id: history ID

        :type jeha_id: str
        :param jeha_id: jeha ID (this should be obtained via
          :meth:`export_history`)

        :type outf: file
        :param outf: output file object, open for writing

        :type chunk_size: int
        :param chunk_size: how many bytes at a time should be read into memory
        """
        url = '%s/exports/%s' % (
            self.gi._make_url(self, module_id=history_id), jeha_id
            )
        r = self.gi.make_get_request(url, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size):
            outf.write(chunk)
