import { Dimensions, useEffect, useState } from 'react';
import { Keyboard } from 'react-native';
import { breakpoints } from '../tokens/breakpoints';

export { useDebounce, useThrottle, useClipboard, useNetwork, useInfiniteScroll, usePagination, usePullToRefresh, usePermissions, useSafeArea } from './utils';

export function useResponsive() {
  const [w, setW] = useState(Dimensions.get('window').width);
  useEffect(() => { const s = Dimensions.addEventListener('change', ({ window }) => setW(window.width)); return () => s?.remove(); }, []);
  return { width: w, isPhone: w < breakpoints.phone, isTablet: w >= breakpoints.phone && w < breakpoints.desktop, isLandscape: w > Dimensions.get('window').height, columns: w < breakpoints.phone ? 1 : w < breakpoints.tablet ? 2 : 3 };
}

export function useKeyboard() {
  const [visible, setVisible] = useState(false); const [height, setHeight] = useState(0);
  useEffect(() => { const s1 = Keyboard.addListener('keyboardDidShow', (e) => { setVisible(true); setHeight(e.endCoordinates.height); }); const s2 = Keyboard.addListener('keyboardDidHide', () => { setVisible(false); setHeight(0); }); return () => { s1.remove(); s2.remove(); }; }, []);
  return { visible, height };
}

export function useBreakpoint() { const [bp, setBp] = useState('phone'); useEffect(() => { const check = () => { const w = Dimensions.get('window').width; setBp(w < breakpoints.phone ? 'phone' : w < breakpoints.tablet ? 'tablet' : 'desktop'); }; check(); const s = Dimensions.addEventListener('change', check); return () => s?.remove(); }, []); return bp; }

export function useReducedMotion() { const [reduced, setReduced] = useState(false); useEffect(() => { /* Check accessibility settings */ }, []); return reduced; }