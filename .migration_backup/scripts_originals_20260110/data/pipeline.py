from __future__ import annotations
from typing import List, Dict, Any, Callable, Awaitable, Optional, Union
import logging
from .source import DataSource

logger = logging.getLogger(__name__)

TransformFunction = Callable[[List[Dict[str, Any]]], Union[List[Dict[str, Any]], Awaitable[List[Dict[str, Any]]]]]

class DataPipeline:
    """
    ETL Pipeline mimicking Pipeline Builder.
    Flow: Extract (Source) -> Transform (Funcs) -> Load (Sink).
    """

    def __init__(self, name: str):
        self.name = name
        self.source: Optional[DataSource] = None
        self.transforms: List[TransformFunction] = []
        self.sinks: List[DataSource] = []

    def extract(self, source: DataSource) -> "DataPipeline":
        """Set the input source."""
        self.source = source
        return self

    def transform(self, func: TransformFunction) -> "DataPipeline":
        """Add a transformation step."""
        self.transforms.append(func)
        return self

    def load(self, sink: DataSource) -> "DataPipeline":
        """Add an output destination."""
        self.sinks.append(sink)
        return self

    async def execute(self) -> None:
        """Run the pipeline."""
        if not self.source:
            raise ValueError("Pipeline has no source defined.")

        logger.info(f"Pipeline '{self.name}': Starting Extraction from {self.source.name}")
        data = await self.source.read()
        logger.info(f"Pipeline '{self.name}': Extracted {len(data)} records")

        for i, tf in enumerate(self.transforms):
            logger.info(f"Pipeline '{self.name}': Executing Transform {i+1}")
            # Support both sync and async transforms
            import inspect
            if inspect.iscoroutinefunction(tf):
                data = await tf(data) # type: ignore
            else:
                data = tf(data) # type: ignore
            logger.info(f"Pipeline '{self.name}': Result count {len(data)}")

        for sink in self.sinks:
            logger.info(f"Pipeline '{self.name}': Loading to {sink.name}")
            await sink.write(data)
            
        logger.info(f"Pipeline '{self.name}': Completed")
