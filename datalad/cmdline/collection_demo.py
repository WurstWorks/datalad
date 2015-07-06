# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""" Collections - HOWTO

This file aims to demonstrate how the classes introduced by PR #157
are intended to be used.
Currently this code will not totally work due to minor issues with the
implementation of these classes, but that's how it will look like and it should
make things clear even without currentlc functioning.

The functions in this file are just there to separate topics.
"""

from os.path import join as opj, expanduser, basename

from ..support.collection import Collection, MetaCollection
from ..support.collectionrepo import CollectionRepo
from ..support.handle import Handle
from ..support.handlerepo import HandleRepo


def get_local_collection_repo():
    # often we need a representation of the local "master" collection:
    return CollectionRepo(expanduser(opj('~', '.datalad', 'localcollection')))


def register_collection(url, name):
    # registering a collection with the master:
    local_col_repo = get_local_collection_repo()
    local_col_repo.git_remote_add(name, url)


def install_handle(dest, col_name=None, handle_name=None, url=None):
    # Basically, all we need is an url of a handle repo; once we got it
    # it's just:
    dst = "path/to/install"
    new_handle = HandleRepo(dst, url)
    master = get_local_collection_repo()
    master.add_handle(new_handle)

    # There a lot of ways to get such an url depending on what we know.
    # It could be the result of a query (see below), we can get it via its name
    # (including the collection it is in) from the master via the repo-classes
    # and we can can get it via the metadata classes.
    # For example:
    url = master.get_handles(col_name)[handle_name]['last_seen']

def install_collection(name, dst):
    # by now, it's not clear whether "installing" a collection
    # (i.e. cloning its repo) will be needed, but anyway:
    local_col_repo = get_local_collection_repo()
    url = local_col_repo.git_get_remote_url(name)
    installed_clone = CollectionRepo(dst, url, name=name)


def new_collection(path, name):
    # Creating a new collection
    col_repo = CollectionRepo(path, name=name)

    # and registering it with the master:
    loc_col_repo = get_local_collection_repo()
    loc_col_repo.git_remote_add(name, path)


def query_local_collection(sparql_str):
    # now, there are several ways to query the metadata
    # let's query the universe for a handle authored by Michael:
    master_repo = get_local_collection_repo()
    universe = MetaCollection(src=master_repo.git_get_branches(),
                                          name="KnownUniverse")

    # 1. we can do this via SPARQL:
    # Within this context, it means to look for a named graph, which states
    # it is a handle and it's authored by Michael:
    # (Note: Not entirely sure about the SPARQL-Syntax yet, but at least it's
    # quite similar to that)
    result = universe.store.query("""
    SELECT ?g ?b {GRAPH ?g
    {?b rdf:type dlns:Handle .
    ?b dlns:authoredBy "Michael Hanke" .}}""")
    # now ?g should be bind to the graph's (i.e. the handle's) name and
    # ?b it's url;
    # we can iterate result object to access its rows:
    for row in result:
        print row

    # let's look only within a certain collection 'foo':
    result = universe['foo'].store.query(sparql_str)
    # But if this is the only query to perform, we don't need to build the
    # graphs of the entire universe:
    result = Collection(src=master_repo.get_backend_from_branch(
        'foo')).store.query(sparql_str)

    # or let's say we have a list of collection names and want to look only
    # within these collections:
    col_list = ['foo', 'bar']
    col_to_query = MetaCollection(src=[master_repo.get_backend_from_branch(name)
                                       for name in col_list],
                                  name="SomeCollections")
    result = col_to_query.store.query(sparql_str)

    # But we don't need to use SPARQL, if we don't want to for some reason.
    # We can iterate over the triples of graph within python and over the
    # graphs within a store. Additionally there "triple-query-methods"
    # available via rdflib:
    from datalad.support.metadatahandler import DLNS
    from rdflib.namespace import RDF
    from rdflib import Literal, Graph
    result = []
    for graph in col_to_query.store.contexts():
        for handle in graph.subjects(RDF.type, DLNS.Handle):
            if (handle, DLNS.authoredBy, Literal("Michael Hanke")) in graph:
                result.append({'name': graph.identifier, 'url': handle})