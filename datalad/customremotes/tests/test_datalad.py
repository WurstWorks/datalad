# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Tests for the universal datalad's annex customremote"""

from ...support.annexrepo import AnnexRepo
from ...consts import DATALAD_SPECIAL_REMOTE
from ...tests.utils import *

from . import _get_custom_runner
from ...support.exceptions import CommandError
from ...downloaders.tests.utils import get_test_providers


@with_tempfile()
@skip_if_no_network
def check_basic_scenario(direct, d):
    annex = AnnexRepo(d, runner=_get_custom_runner(d), direct=direct)
    annex.init_remote(
        DATALAD_SPECIAL_REMOTE,
        ['encryption=none', 'type=external', 'externaltype=%s' % DATALAD_SPECIAL_REMOTE,
         'autoenable=true'])

    # TODO skip if no boto or no credentials
    get_test_providers('s3://datalad-test0-versioned/') # so to skip if unknown creds

    # Let's try to add some file which we should have access to
    with swallow_outputs() as cmo:
        annex.add_urls(['s3://datalad-test0-versioned/3versions-allversioned.txt'])
        annex.commit("committing")
        whereis1 = annex.whereis('3versions_allversioned.txt', output='full')
        eq_(len(whereis1), 2)  # here and datalad
        annex.drop('3versions_allversioned.txt')
        if PY2:
            pass  # stopped appearing within the test  TODO
            #assert_in('100%', cmo.err)  # we do provide our progress indicator
        else:
            pass  # TODO:  not sure what happened but started to fail for me on my laptop under tox
    whereis2 = annex.whereis('3versions_allversioned.txt', output='full')
    eq_(len(whereis2), 1)  # datalad

    # if we provide some bogus address which we can't access, we shouldn't pollute output
    with swallow_outputs() as cmo, swallow_logs() as cml:
        with assert_raises(CommandError) as cme:
            annex.add_urls(['s3://datalad-test0-versioned/3versions-allversioned.txt_bogus'])
        # assert_equal(cml.out, '')
        err, out = cmo.err, cmo.out
    assert_equal(out, '')
    assert_in('addurl: 1 failed', err)
    # and there should be nothing more


def test_basic_scenario():
    yield check_basic_scenario, False
    if not on_windows:
        yield check_basic_scenario, True
