from __future__ import annotations

import ast
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from langchain_community.document_loaders.base import BaseBlobParser
from langchain_community.document_loaders.blob_loaders.schema import Blob, BlobLoader
from langchain_community.document_loaders.parsers.language.code_segmenter import (
    CodeSegmenter,
)
from langchain_community.document_loaders.parsers.language.language_parser import (
    LANGUAGE_EXTENSIONS,
    Language,
)
from langchain_community.document_loaders.parsers.registry import get_parser
from langchain_core.documents import Document

from langchain_community.document_loaders.blob_loaders.file_system import _make_iterator
from langchain_community.document_loaders.generic import (
    GenericLoader as BaseGenericLoader,
)


class PythonSegmenter(CodeSegmenter):
    """Code segmenter for `Python`."""

    def __init__(self, code: str):
        super().__init__(code)
        self.source_lines = self.code.splitlines()

    def is_valid(self) -> bool:
        try:
            ast.parse(self.code)
            return True
        except SyntaxError:
            return False

    def _extract_code(self, node: Any) -> Tuple[int, str]:
        start = node.lineno - 1
        end = node.end_lineno
        return start, "\n".join(self.source_lines[start:end])

    def extract_functions_classes(self) -> Iterator[Tuple[int, str]]:
        tree = ast.parse(self.code)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start, code = self._extract_code(node)
                yield start, code

    def simplify_code(self) -> str:
        tree = ast.parse(self.code)
        simplified_lines = self.source_lines[:]

        indices_to_del: List[Tuple[int, int]] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start, end = node.lineno - 1, node.end_lineno
                simplified_lines[start] = f"# Code for: {simplified_lines[start]}"
                assert isinstance(end, int)
                indices_to_del.append((start + 1, end))

        for start, end in reversed(indices_to_del):
            del simplified_lines[start + 0 : end]

        return "\n".join(simplified_lines)


LANGUAGE_SEGMENTERS: Dict[str, Any] = {
    "python": PythonSegmenter,
}

if TYPE_CHECKING:
    from langchain_text_splitters import TextSplitter

T = TypeVar("T")

_PathLike = Union[str, Path]

DEFAULT = Literal["default"]


class FileSystemBlobLoader(BlobLoader):
    """Load blobs in the local file system.

    Example:

    .. code-block:: python

        from langchain_community.document_loaders.blob_loaders import FileSystemBlobLoader
        loader = FileSystemBlobLoader("/path/to/directory")
        for blob in loader.yield_blobs():
            print(blob)  # noqa: T201
    """  # noqa: E501

    def __init__(
        self,
        path: Union[str, Path],
        *,
        glob: str = "**/[!.]*",
        exclude: Sequence[str] = (),
        suffixes: Optional[Sequence[str]] = None,
        show_progress: bool = False,
    ) -> None:
        """Initialize with a path to directory and how to glob over it.

        Args:
            path: Path to directory to load from or path to file to load.
                  If a path to a file is provided, glob/exclude/suffixes are ignored.
            glob: Glob pattern relative to the specified path
                  by default set to pick up all non-hidden files
            exclude: patterns to exclude from results, use glob syntax
            suffixes: Provide to keep only files with these suffixes
                      Useful when wanting to keep files with different suffixes
                      Suffixes must include the dot, e.g. ".txt"
            show_progress: If true, will show a progress bar as the files are loaded.
                           This forces an iteration through all matching files
                           to count them prior to loading them.

        Examples:

            .. code-block:: python
                from langchain_community.document_loaders.blob_loaders import FileSystemBlobLoader

                # Load a single file.
                loader = FileSystemBlobLoader("/path/to/file.txt")

                # Recursively load all text files in a directory.
                loader = FileSystemBlobLoader("/path/to/directory", glob="**/*.txt")

                # Recursively load all non-hidden files in a directory.
                loader = FileSystemBlobLoader("/path/to/directory", glob="**/[!.]*")

                # Load all files in a directory without recursion.
                loader = FileSystemBlobLoader("/path/to/directory", glob="*")

                # Recursively load all files in a directory, except for py or pyc files.
                loader = FileSystemBlobLoader(
                    "/path/to/directory",
                    glob="**/*.txt",
                    exclude=["**/*.py", "**/*.pyc"]
                )
        """  # noqa: E501
        if isinstance(path, Path):
            _path = path
        elif isinstance(path, str):
            _path = Path(path)
        else:
            raise TypeError(f"Expected str or Path, got {type(path)}")

        self.path = _path.expanduser()  # Expand user to handle ~
        self.glob = glob
        self.suffixes = set(suffixes or [])
        self.show_progress = show_progress
        self.exclude = exclude

    def yield_blobs(
        self,
    ) -> Iterable[Blob]:
        """Yield blobs that match the requested pattern."""
        iterator = _make_iterator(
            length_func=self.count_matching_files, show_progress=self.show_progress
        )

        for path in iterator(self._yield_paths()):
            blob = Blob.from_path(path)

            yield blob

    def _yield_paths(self) -> Iterable[Path]:
        """Yield paths that match the requested pattern."""
        if self.path.is_file():
            yield self.path
            return

        paths = self.path.glob(self.glob)
        for path in paths:
            if self.exclude:
                if any(path.match(glob) for glob in self.exclude):
                    continue
            if path.is_file():
                if self.suffixes and path.suffix not in self.suffixes:
                    continue
                yield path

    def count_matching_files(self) -> int:
        """Count files that match the pattern without loading them."""
        # Carry out a full iteration to count the files without
        # materializing anything expensive in memory.
        num = 0
        for _ in self._yield_paths():
            num += 1
        return num


class GenericLoader(BaseGenericLoader):
    """Generic Document Loader.

    A generic document loader that allows combining an arbitrary blob loader with
    a blob parser.

    Examples:

        Parse a specific PDF file:

        .. code-block:: python

            from langchain_community.document_loaders import GenericLoader
            from langchain_community.document_loaders.parsers.pdf import PyPDFParser

            # Recursively load all text files in a directory.
            loader = GenericLoader.from_filesystem(
                "my_lovely_pdf.pdf",
                parser=PyPDFParser()
            )

       .. code-block:: python

            from langchain_community.document_loaders import GenericLoader
            from langchain_community.document_loaders.blob_loaders import FileSystemBlobLoader


            loader = GenericLoader.from_filesystem(
                path="path/to/directory",
                glob="**/[!.]*",
                suffixes=[".pdf"],
                show_progress=True,
            )

            docs = loader.lazy_load()
            next(docs)

    Example instantiations to change which files are loaded:

    .. code-block:: python

        # Recursively load all text files in a directory.
        loader = GenericLoader.from_filesystem("/path/to/dir", glob="**/*.txt")

        # Recursively load all non-hidden files in a directory.
        loader = GenericLoader.from_filesystem("/path/to/dir", glob="**/[!.]*")

        # Load all files in a directory without recursion.
        loader = GenericLoader.from_filesystem("/path/to/dir", glob="*")

    Example instantiations to change which parser is used:

    .. code-block:: python

        from langchain_community.document_loaders.parsers.pdf import PyPDFParser

        # Recursively load all text files in a directory.
        loader = GenericLoader.from_filesystem(
            "/path/to/dir",
            glob="**/*.pdf",
            parser=PyPDFParser()
        )

    """  # noqa: E501

    def __init__(
        self,
        blob_loader: BlobLoader,
        blob_parser: BaseBlobParser,
    ) -> None:
        """A generic document loader.

        Args:
            blob_loader: A blob loader which knows how to yield blobs
            blob_parser: A blob parser which knows how to parse blobs into documents
        """
        self.blob_loader = blob_loader
        self.blob_parser = blob_parser

    def lazy_load(
        self,
    ) -> Iterator[Document]:
        """Load documents lazily. Use this when working at a large scale."""
        for blob in self.blob_loader.yield_blobs():
            yield from self.blob_parser.lazy_parse(blob)

    def load_and_split(
        self, text_splitter: Optional[TextSplitter] = None
    ) -> List[Document]:
        """Load all documents and split them into sentences."""
        raise NotImplementedError(
            "Loading and splitting is not yet implemented for generic loaders. "
            "When they will be implemented they will be added via the initializer. "
            "This method should not be used going forward."
        )

    @classmethod
    def from_filesystem(
        cls,
        path: _PathLike,
        *,
        glob: str = "**/[!.]*",
        exclude: Sequence[str] = (),
        suffixes: Optional[Sequence[str]] = None,
        show_progress: bool = False,
        parser: Union[DEFAULT, BaseBlobParser] = "default",
        parser_kwargs: Optional[dict] = None,
    ) -> GenericLoader:
        """Create a generic document loader using a filesystem blob loader.

        Args:
            path: The path to the directory to load documents from OR the path to a
                  single file to load. If this is a file, glob, exclude, suffixes
                    will be ignored.
            glob: The glob pattern to use to find documents.
            suffixes: The suffixes to use to filter documents. If None, all files
                      matching the glob will be loaded.
            exclude: A list of patterns to exclude from the loader.
            show_progress: Whether to show a progress bar or not (requires tqdm).
                           Proxies to the file system loader.
            parser: A blob parser which knows how to parse blobs into documents,
                    will instantiate a default parser if not provided.
                    The default can be overridden by either passing a parser or
                    setting the class attribute `blob_parser` (the latter
                    should be used with inheritance).
            parser_kwargs: Keyword arguments to pass to the parser.

        Returns:
            A generic document loader.
        """
        blob_loader = FileSystemBlobLoader(
            path,
            glob=glob,
            exclude=exclude,
            suffixes=suffixes,
            show_progress=show_progress,
        )
        if isinstance(parser, str):
            if parser == "default":
                try:
                    # If there is an implementation of get_parser on the class, use it.
                    blob_parser = cls.get_parser(**(parser_kwargs or {}))
                except NotImplementedError:
                    # if not then use the global registry.
                    blob_parser = get_parser(parser)
            else:
                blob_parser = get_parser(parser)
        else:
            blob_parser = parser
        return cls(blob_loader, blob_parser)

    @staticmethod
    def get_parser(**kwargs: Any) -> BaseBlobParser:
        """Override this method to associate a default parser with the class."""
        raise NotImplementedError()


class LanguageParser(BaseBlobParser):
    """Parse using the respective programming language syntax.

    Each top-level function and class in the code is loaded into separate documents.
    Furthermore, an extra document is generated, containing the remaining top-level code
    that excludes the already segmented functions and classes.

    This approach can potentially improve the accuracy of QA models over source code.

    The supported languages for code parsing are:

    - C: "c" (*)
    - C++: "cpp" (*)
    - C#: "csharp" (*)
    - COBOL: "cobol"
    - Go: "go" (*)
    - Java: "java" (*)
    - JavaScript: "js" (requires package `esprima`)
    - Kotlin: "kotlin" (*)
    - Lua: "lua" (*)
    - Perl: "perl" (*)
    - Python: "python"
    - Ruby: "ruby" (*)
    - Rust: "rust" (*)
    - Scala: "scala" (*)
    - TypeScript: "ts" (*)

    Items marked with (*) require the packages `tree_sitter` and
    `tree_sitter_languages`. It is straightforward to add support for additional
    languages using `tree_sitter`, although this currently requires modifying LangChain.

    The language used for parsing can be configured, along with the minimum number of
    lines required to activate the splitting based on syntax.

    If a language is not explicitly specified, `LanguageParser` will infer one from
    filename extensions, if present.

    Examples:

       .. code-block:: python

            from langchain_community.document_loaders.generic import GenericLoader
            from langchain_community.document_loaders.parsers import LanguageParser

            loader = GenericLoader.from_filesystem(
                "./code",
                glob="**/*",
                suffixes=[".py", ".js"],
                parser=LanguageParser()
            )
            docs = loader.load()

        Example instantiations to manually select the language:

        .. code-block:: python


            loader = GenericLoader.from_filesystem(
                "./code",
                glob="**/*",
                suffixes=[".py"],
                parser=LanguageParser(language="python")
            )

        Example instantiations to set number of lines threshold:

        .. code-block:: python

            loader = GenericLoader.from_filesystem(
                "./code",
                glob="**/*",
                suffixes=[".py"],
                parser=LanguageParser(parser_threshold=200)
            )
    """

    def __init__(self, language: Optional[Language] = None, parser_threshold: int = 0):
        """
        Language parser that split code using the respective language syntax.

        Args:
            language: If None (default), it will try to infer language from source.
            parser_threshold: Minimum lines needed to activate parsing (0 by default).
        """
        if language and language not in LANGUAGE_SEGMENTERS:
            raise Exception(f"No parser available for {language}")
        self.language = language
        self.parser_threshold = parser_threshold

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        code = blob.as_string()

        language = self.language or (
            LANGUAGE_EXTENSIONS.get(blob.source.rsplit(".", 1)[-1])
            if isinstance(blob.source, str)
            else None
        )

        if language is None:
            yield Document(
                page_content=code,
                metadata={
                    "source": blob.source,
                    "start_line": 1,  # Default start line
                },
            )
            return

        if self.parser_threshold >= len(code.splitlines()):
            yield Document(
                page_content=code,
                metadata={
                    "source": blob.source,
                    "language": language,
                    "start_line": 1,  # Default start line
                },
            )
            return

        self.Segmenter = LANGUAGE_SEGMENTERS[language]
        segmenter = self.Segmenter(blob.as_string())
        if not segmenter.is_valid():
            yield Document(
                page_content=code,
                metadata={
                    "source": blob.source,
                    "start_line": 1,  # Default start line
                },
            )
            return

        for start_line, functions_classes in segmenter.extract_functions_classes():
            yield Document(
                page_content=functions_classes,
                metadata={
                    "source": blob.source,
                    "content_type": "functions_classes",
                    "language": language,
                    "start_line": start_line + 1,  # Adjust start line
                },
            )
        yield Document(
            page_content=segmenter.simplify_code(),
            metadata={
                "source": blob.source,
                "content_type": "simplified_code",
                "language": language,
                "start_line": 1,  # Default start line
            },
        )
