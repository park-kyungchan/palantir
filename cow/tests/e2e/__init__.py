"""
End-to-end tests for Math Image Parsing Pipeline.

These tests verify the complete pipeline from image input to final export,
including all 8 stages:
    A. Ingestion -> B. TextParse -> C. VisionParse -> D. Alignment
                                                          |
    H. Export <- G. HumanReview <- F. Regeneration <- E. SemanticGraph

Test Categories:
- Full Pipeline Tests: Complete workflow with different image types
- Error Handling Tests: Recovery and failure scenarios
- Export Format Tests: Verification of all export formats
- Performance Tests: Timing and throughput verification
"""
