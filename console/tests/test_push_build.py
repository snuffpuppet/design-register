import unittest, tempfile, os, shutil
import server as S


class Stub:
    """The handler methods only use self for other methods, so an instance without a socket will do."""
    for _n in ("push_build",):
        locals()[_n] = getattr(S.H, _n, None)


class PushBuildNoConfig(unittest.TestCase):
    """When confluence.json is not visible to the console (a plain container mount with no repo root
    bind, or a checkout that has moved it), push_build refuses with a message that says what to run
    instead, and never attempts to import push-pages.py."""

    def setUp(self):
        self.saved_here = S.HERE
        self.d = tempfile.mkdtemp()
        S.HERE = os.path.join(self.d, "console")   # so HERE/../confluence.json does not exist
        os.makedirs(S.HERE)
        self.h = Stub()

    def tearDown(self):
        S.HERE = self.saved_here
        shutil.rmtree(self.d)

    def test_refuses_with_a_message_naming_the_makefile_target(self):
        with self.assertRaises(ValueError) as cm:
            self.h.push_build()
        self.assertEqual(str(cm.exception),
                          "confluence.json is not visible to the console; run make push-pages ENG=<engagement> from the repository instead.")


if __name__ == "__main__":
    unittest.main()
