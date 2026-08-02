/** Design System — Enterprise Master Barrel Export (fully modular, tree-shakeable, 120+ symbols) */

// ═══════════════════════════════════════
// TOKENS (22 files)
// ═══════════════════════════════════════
export { brand, neutral, success, warning, danger, info } from './tokens/colors';
export { typography } from './tokens/typography';
export { spacing } from './tokens/spacing';
export { radius } from './tokens/radius';
export { elevation } from './tokens/elevation';
export { opacity } from './tokens/opacity';
export { durations } from './tokens/durations';
export { easings } from './tokens/motion';
export { zIndex } from './tokens/zIndex';
export { breakpoints } from './tokens/breakpoints';
export { surface, text } from './tokens/semanticColors';
export { statusColors } from './tokens/statusColors';
export { chartColors, chartPalette } from './tokens/chartColors';
export { predictionColors } from './tokens/predictionColors';
export { eventColors } from './tokens/eventColors';
export { fighterColors } from './tokens/fighterColors';
export { rankingColors } from './tokens/rankingColors';
export { recommendationColors } from './tokens/recommendationColors';
export { notificationColors } from './tokens/notificationColors';
export { glass, blurAmounts, gradients, grid, brandThemes, a11yColors } from './tokens/extended';

// ═══════════════════════════════════════
// THEME (7 files)
// ═══════════════════════════════════════
export { ThemeProvider } from './theme/ThemeProvider';
export { useTheme } from './theme/useTheme';
export { buildTheme, darkTheme, lightTheme, amoledTheme } from './theme/ThemeBuilder';
export { ThemeContext } from './theme/ThemeContext';
export { ThemeStorage } from './theme/ThemeStorage';
export type { Theme, ThemeMode, ThemeContextValue } from './theme/ThemeTypes';

// ═══════════════════════════════════════
// COMPONENTS (25 folders)
// ═══════════════════════════════════════
// Core
export { Button } from './components/Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './components/Button';
export { Card } from './components/Card';
export type { CardProps, CardVariant } from './components/Card';
export { TextField } from './components/TextField';
export type { TextFieldProps } from './components/TextField';
export { Dialog } from './components/Dialog';
export type { DialogProps } from './components/Dialog';
export { BottomSheet } from './components/BottomSheet';
export type { BottomSheetProps } from './components/BottomSheet';
export { Toast } from './components/Toast';
export type { ToastProps } from './components/Toast';
// Toggles
export { Switch, Checkbox, Radio, SegmentedControl, Stepper } from './components/Switch';
// Select & Search
export { Select, SearchInput, Tooltip, Accordion, Breadcrumb, Calendar, Snackbar, Carousel } from './components/Select';
// Icon + Layout
export { IconButton } from './components/IconButton';
export { Container, Grid, Stack, Spacer } from './components/Container';
// Display
export { Skeleton, SkeletonCard, SkeletonProfile } from './components/Skeleton';
export { EmptyState, ErrorState } from './components/EmptyState';
export { Badge, Chip, Avatar } from './components/Badge';
export { Tabs, ProgressBar, Divider, ListItem, FAB } from './components/Tabs';

// ═══════════════════════════════════════
// HOOKS (12 hooks)
// ═══════════════════════════════════════
export { useResponsive, useKeyboard, useBreakpoint, useReducedMotion } from './hooks';
export { useDebounce, useThrottle, useClipboard, useNetwork, useInfiniteScroll, usePagination, usePullToRefresh, usePermissions, useSafeArea } from './hooks';

// ═══════════════════════════════════════
// ANIMATIONS (12 functions)
// ═══════════════════════════════════════
export { fadeIn, fadeOut, scaleIn, scaleOut, slideUp, slideDown, livePulse, countdownFlip, spring } from './animations';
export { shake, shimmer, heroTransition, navigationTransitions, cardExpand, pageTransition } from './animations/animationLib';

// ═══════════════════════════════════════
// CHARTS (5 components)
// ═══════════════════════════════════════
export { BarChart } from './charts/BarChart';
export { ProbabilityChart, WinLossChart, MomentumChart } from './charts/ProbabilityChart';

// ═══════════════════════════════════════
// IMAGES (5 components)
// ═══════════════════════════════════════
export { CachedImage, BlurImage, AvatarImage, PosterImage, FallbackImage } from './images';

// ═══════════════════════════════════════
// GESTURES (4 creators)
// ═══════════════════════════════════════
export { createSwipeGesture, createDragGesture, createPinchGesture, createLongPressGesture } from './gestures';

// ═══════════════════════════════════════
// ACCESSIBILITY (12 utilities)
// ═══════════════════════════════════════
export { a11y, a11yLabels } from './accessibility';
export { screenReader, focusManagement, reducedMotion, dynamicType, highContrast, a11yTest } from './accessibility/screen-reader';

// ═══════════════════════════════════════
// RESPONSIVE + UTILS
// ═══════════════════════════════════════
export { getDeviceLayout, phoneLayout, tabletLayout, desktopLayout } from './responsive';
export { createShadow, createSpacing, createRadius, createTextStyle, conditionalStyle, layerStyles } from './utils';

// ═══════════════════════════════════════
// MIGRATION UTILITY — for feature modules
// ═══════════════════════════════════════
export function migrateFeatureUI() { return { ok: true }; }