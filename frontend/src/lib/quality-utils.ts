/**
 * Quality Report Utility Functions
 *
 * Maps technical confidence scores to user-friendly messages
 * per Epic 4 Retrospective Action 1.5
 */

/**
 * Get user-friendly quality level message based on confidence score
 *
 * @param confidence - Overall confidence score (0-100)
 * @returns User-friendly quality message with emoji
 */
export function getQualityLevelMessage(confidence: number): string {
  if (confidence >= 95) return "Excellent - All elements preserved perfectly ✅";
  if (confidence >= 85) return "Very Good - Nearly all elements preserved ✅";
  if (confidence >= 75) return "Good - Most elements preserved ⚠️";
  if (confidence >= 60) return "Fair - Some elements may need review ⚠️";
  return "Review Required - Significant issues detected ❌";
}

/**
 * Get emoji indicator for quality level
 *
 * @param confidence - Overall confidence score (0-100)
 * @returns Emoji representing quality level
 */
export function getQualityEmoji(confidence: number): string {
  if (confidence >= 85) return "✅";
  if (confidence >= 60) return "⚠️";
  return "❌";
}

/**
 * Get element-specific message based on count and confidence
 *
 * @param elementType - Type of element (tables, images, equations, chapters)
 * @param count - Number of elements detected
 * @param avgConfidence - Average confidence score (optional)
 * @returns User-friendly element message
 */
export function getElementMessage(
  elementType: "tables" | "images" | "equations" | "chapters",
  count: number,
  avgConfidence?: number
): string {
  if (count === 0) return `No ${elementType} detected`;

  // Images and chapters don't have confidence scores
  if (elementType === "images" || elementType === "chapters") {
    return `${count} ${elementType} detected and preserved`;
  }

  // Tables and equations have confidence scores
  if (avgConfidence === undefined) return `${count} ${elementType} detected`;

  if (avgConfidence >= 90) {
    return `${count} ${elementType} detected and preserved`;
  } else if (avgConfidence >= 70) {
    const reviewCount = Math.ceil(count * (1 - avgConfidence / 100));
    return `${count} ${elementType} detected, ${reviewCount} may need review`;
  } else {
    const reviewCount = Math.ceil(count * 0.5);
    return `${count} ${elementType} detected, ${reviewCount} require manual verification`;
  }
}

/**
 * Get color coding for confidence score
 *
 * @param confidence - Confidence score (0-100)
 * @returns Color name for UI styling
 */
export function getConfidenceColor(confidence: number): "green" | "yellow" | "red" {
  if (confidence >= 95) return "green";
  if (confidence >= 75) return "yellow";
  return "red";
}

/**
 * Get progress bar color class for confidence score
 *
 * @param confidence - Confidence score (0-100)
 * @returns Tailwind CSS class for progress bar color
 */
export function getConfidenceProgressColor(confidence: number): string {
  if (confidence >= 95) return "bg-green-500";
  if (confidence >= 75) return "bg-yellow-500";
  return "bg-red-500";
}
