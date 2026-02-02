"""
Test script for Merkle tree change detection.
"""

from code_chatbot.ingestion.merkle_tree import MerkleTree
from pathlib import Path
import tempfile
import shutil

def test_merkle_tree():
    """Test Merkle tree change detection."""
    
    # Create a temporary directory with some files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create initial files
        (tmpdir / "file1.py").write_text("print('hello')")
        (tmpdir / "file2.py").write_text("print('world')")
        (tmpdir / "subdir").mkdir()
        (tmpdir / "subdir" / "file3.py").write_text("print('test')")
        
        # Build initial tree
        merkle = MerkleTree()
        tree1 = merkle.build_tree(str(tmpdir))
        
        print(f"✅ Built initial Merkle tree")
        print(f"   Root hash: {tree1.hash[:16]}...")
        
        # Modify a file
        (tmpdir / "file1.py").write_text("print('hello world')")
        
        # Add a new file
        (tmpdir / "file4.py").write_text("print('new')")
        
        # Delete a file
        (tmpdir / "file2.py").unlink()
        
        # Build new tree
        tree2 = merkle.build_tree(str(tmpdir))
        
        # Compare
        changes = merkle.compare_trees(tree1, tree2)
        
        print(f"\\n✅ Change detection complete:")
        print(f"   {changes.summary()}")
        print(f"   Added: {changes.added}")
        print(f"   Modified: {changes.modified}")
        print(f"   Deleted: {changes.deleted}")
        
        # Verify results
        assert "file4.py" in changes.added, "Should detect new file"
        assert "file1.py" in changes.modified, "Should detect modified file"
        assert "file2.py" in changes.deleted, "Should detect deleted file"
        assert "subdir/file3.py" in changes.unchanged, "Should detect unchanged file"
        
        print(f"\\n✅ All assertions passed!")

if __name__ == "__main__":
    test_merkle_tree()
