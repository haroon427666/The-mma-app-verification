# Design System — Migration Reference

## Feature Module → Design System Component Map

### Events Module
| Before (custom) | After (design system) |
|---|---|
| `TouchableOpacity` with text | `<Button>` |
| `View` with padding+borderRadius | `<Card>` |
| Custom modal | `<Dialog>` or `<BottomSheet>` |
| Custom skeleton | `<SkeletonCard>` |
| Inline error text | `<ErrorState>` |

### Fighters Module
| Before (custom) | After (design system) |
|---|---|
| Custom filter buttons | `<Chip>` or `<SegmentedControl>` |
| Fighter list row | `<ListItem>` |
| Profile header | `<Card>` + `<Avatar>` |
| Weight class filters | `<Tabs>` |
| Favorite toggle | `<Button variant="ghost">` |

### Rankings Module
| Before (custom) | After (design system) |
|---|---|
| Rank badge | `<Badge>` |
| Division selector | `<SegmentedControl>` |
| P4P/Division/GOAT tabs | `<Tabs>` |
| Ranking card | `<ListItem>` with rank badge |
| Champion badge | `<Badge color="#F59E0B">` |

### Predictions Module
| Before (custom) | After (design system) |
|---|---|
| Win probability display | `<ProbabilityChart>` |
| Confidence indicator | `<Badge>` with prediction colors |
| Finish breakdown bars | `<ProgressBar>` |
| Key factors list | `<ListItem>` |
| Save/unsave toggle | `<Button variant="ghost">` |

### All Modules — Standard Replacements
| Replace This | With This |
|---|---|
| `{ color: '#1A1A2E' }` | `{ backgroundColor: palette.surface.card }` |
| `{ padding: 16 }` | `spacing.md` |
| `{ borderRadius: 12 }` | `radius.md` |
| `{ fontSize: 22, fontWeight: '700' }` | `typography.title` |
| `{ fontSize: 14, color: '#9CA3AF' }` | `{ ...typography.caption, color: palette.text.secondary }` |
| `{ marginBottom: 24 }` | `spacing.lg` |
| `{ borderWidth: 0.5, borderColor: '#2A2A3E' }` | `{ borderWidth: 0.5, borderColor: palette.surface.border }` |

## Quick Migration Check
After migration, verify:
1. No hardcoded colors (search for `'#` in component files)
2. No hardcoded padding (search for `padding:` without `spacing.`)
3. No hardcoded font sizes (search for `fontSize:` without `typography.`)
4. All imports are from `@/design-system`