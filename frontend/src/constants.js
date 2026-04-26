/**
 * Shared frontend constants.
 *
 * File-validation rules here mirror the backend config so that the UI
 * can give instant feedback before a network round-trip is attempted.
 */

/** MIME types accepted for wiki document uploads. */
export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

/** Maximum allowed file size in bytes (10 MB). */
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

/** Human-readable label shown in validation messages. */
export const ALLOWED_FILE_LABEL = 'PDF, DOC, DOCX files up to 10 MB each';

/** Map from lowercase file extension to display emoji. */
export const FILE_ICON_MAP = {
  pdf: '📄',
  doc: '📝',
  docx: '📝',
};

/** Fallback icon for unknown file types. */
export const DEFAULT_FILE_ICON = '📄';
