import { Dimensions, ScaledSize } from 'react-native';
import { breakpoints } from '../tokens/breakpoints';

export function getDeviceLayout(dims?: ScaledSize) {
  const { width, height } = dims || Dimensions.get('window');
  const isPhone = width < breakpoints.tablet;
  const isTablet = width >= breakpoints.tablet && width < breakpoints.desktop;
  const isDesktop = width >= breakpoints.desktop;
  const isLandscape = width > height;
  return { width, height, isPhone, isTablet, isDesktop, isLandscape, columns: isPhone ? 1 : isTablet ? 2 : 3 };
}

export const phoneLayout = { maxWidth: breakpoints.phone, padding: 16 };
export const tabletLayout = { maxWidth: breakpoints.tablet, padding: 24 };
export const desktopLayout = { maxWidth: 1200, padding: 32 };