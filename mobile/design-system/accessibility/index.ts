export const a11y = {
  button: (label: string) => ({ accessible: true, accessibilityRole: 'button' as const, accessibilityLabel: label }),
  image: (desc: string) => ({ accessible: true, accessibilityRole: 'image' as const, accessibilityLabel: desc }),
  header: (label: string) => ({ accessible: true, accessibilityRole: 'header' as const, accessibilityLabel: label }),
  link: (label: string) => ({ accessible: true, accessibilityRole: 'link' as const, accessibilityLabel: label }),
  search: (label: string) => ({ accessible: true, accessibilityRole: 'search' as const, accessibilityLabel: label }),
  tab: (label: string, selected: boolean) => ({ accessible: true, accessibilityRole: 'tab' as const, accessibilityLabel: label, accessibilityState: { selected } }),
  list: () => ({ accessible: true, accessibilityRole: 'list' as const }),
  listItem: (label: string) => ({ accessible: true, accessibilityRole: 'button' as const, accessibilityLabel: label }),
  liveRegion: () => ({ accessibilityLiveRegion: 'polite' as const }),
  announcement: () => ({ accessibilityLiveRegion: 'assertive' as const }),
} as const;

export const a11yLabels = {
  close: 'Close',
  back: 'Go back',
  delete: 'Delete',
  share: 'Share',
  save: 'Save',
  edit: 'Edit',
  search: 'Search',
  clear: 'Clear',
  retry: 'Retry',
  refresh: 'Refresh',
  dismiss: 'Dismiss',
};