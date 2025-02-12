import unittest
import os
import shutil
from src.domain.classes.FileSystemMacOSClass import FileSystemMacOS


class TestFileSystemMacOS(unittest.TestCase):

    def setUp(self):
        """
        Set up temporary directories and a FileSystemMacOS instance for testing.
        """
        self.sandbox_dir = os.path.abspath("tests/test_filesystem_macos__sandbox")
        self.folder_a = os.path.join(self.sandbox_dir, "FolderA")
        self.folder_b = os.path.join(self.sandbox_dir, "FolderB")
        self.file_system = FileSystemMacOS()

        # Ensure the sandbox directory is clean
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)

        # Create FolderA and FolderB
        os.makedirs(self.folder_a, exist_ok=True)
        os.makedirs(self.folder_b, exist_ok=True)

        # Populate FolderA with random directories and files
        for i in range(3):  # Create random directories
            os.makedirs(os.path.join(self.folder_a, f"DA{i+1}"))
        for i in range(3):  # Create random text files
            with open(os.path.join(self.folder_a, f"fa{i+1}.txt"), "w") as f:
                f.write(f"Content of file fa{i+1}.txt")

    def tearDown(self):
        """
        Clean up after tests by removing the sandbox directory.
        """
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)

    def test_deep_tree_move(self):
        """
        Test the functionality of deep_tree_move method.
        """
        # Populate FolderB with a common directory
        os.makedirs(os.path.join(self.folder_b, "DA1"), exist_ok=True)
        with open(os.path.join(self.folder_b, "DA1", "existing_in_b.txt"), "w") as f:
            f.write("Existing content in FolderB/DA1")

        # Add files and directories to FolderA
        with open(os.path.join(self.folder_a, "fa1.txt"), "w") as f:
            f.write("Content of file fa1.txt")
        os.makedirs(os.path.join(self.folder_a, "DA1"), exist_ok=True)
        with open(os.path.join(self.folder_a, "DA1", "file_in_a.txt"), "w") as f:
            f.write("Content in FolderA/DA1")

        # Perform deep_tree_move
        self.file_system.deep_tree_move(self.folder_a, self.folder_b)

        # Check FolderA is deleted
        self.assertFalse(os.path.exists(self.folder_a))

        # Verify FolderB contains all moved items
        folder_b_items = os.listdir(self.folder_b)
        self.assertIn("fa1.txt", folder_b_items)  # File from FolderA
        self.assertIn("DA1", folder_b_items)     # Directory from FolderA

        # Verify merged content in DA1
        da1_files = os.listdir(os.path.join(self.folder_b, "DA1"))
        self.assertIn("existing_in_b.txt", da1_files)  # Original file in FolderB/DA1
        self.assertIn("file_in_a.txt", da1_files)     # Moved file from FolderA/DA1

        # Verify content of moved files
        with open(os.path.join(self.folder_b, "fa1.txt"), "r") as f:
            self.assertEqual(f.read(), "Content of file fa1.txt")

        with open(os.path.join(self.folder_b, "DA1", "file_in_a.txt"), "r") as f:
            self.assertEqual(f.read(), "Content in FolderA/DA1")


    def test_merge_folders(self):
        """
        Test merging FolderA into FolderB.
        """
        # Add files and directories to FolderB
        os.makedirs(os.path.join(self.folder_b, "DA1"), exist_ok=True)
        with open(os.path.join(self.folder_b, "DA1", "file_b.txt"), "w") as f:
            f.write("File from FolderB")
        with open(os.path.join(self.folder_b, "fb1.txt"), "w") as f:
            f.write("Unique file in FolderB")

        # Move FolderA to FolderB
        self.file_system.deep_tree_move(self.folder_a, self.folder_b)

        # Verify FolderB has merged content
        self.assertTrue(os.path.exists(os.path.join(self.folder_b, "DA1")))
        self.assertTrue(os.path.exists(os.path.join(self.folder_b, "DA2")))
        self.assertTrue(os.path.exists(os.path.join(self.folder_b, "DA3")))
        self.assertTrue(os.path.exists(os.path.join(self.folder_b, "fb1.txt")))

        # Check merged directory contents
        da1_files = os.listdir(os.path.join(self.folder_b, "DA1"))
        self.assertIn("file_b.txt", da1_files)

    def test_overwrite_files(self):
        """
        Test overwriting files during deep_tree_move.
        """
        # Add a conflicting file to FolderB
        with open(os.path.join(self.folder_b, "fa1.txt"), "w") as f:
            f.write("Old content in FolderB")

        # Perform deep_tree_move
        self.file_system.deep_tree_move(self.folder_a, self.folder_b)

        # Verify the file in FolderB is overwritten
        with open(os.path.join(self.folder_b, "fa1.txt"), "r") as f:
            content = f.read()
        self.assertEqual(content, "Content of file fa1.txt")

    def test_empty_source(self):
        """
        Test deep_tree_move when the source is empty.
        """
        # Clear FolderA
        shutil.rmtree(self.folder_a)
        os.makedirs(self.folder_a, exist_ok=True)

        # Perform deep_tree_move
        self.file_system.deep_tree_move(self.folder_a, self.folder_b)

        # Verify FolderB remains unchanged
        self.assertTrue(os.path.exists(self.folder_b))
        self.assertEqual(len(os.listdir(self.folder_b)), 0)

    def test_nonexistent_source(self):
        """
        Test deep_tree_move when the source does not exist.
        """
        # Delete FolderA
        shutil.rmtree(self.folder_a)

        # Expect ValueError
        with self.assertRaises(ValueError):
            self.file_system.deep_tree_move(self.folder_a, self.folder_b)


if __name__ == "__main__":
    unittest.main()