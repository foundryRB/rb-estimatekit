import type { ReactNode } from 'react';
import { useAppearance } from '../vodafone/useAppearance';

/** Compatibility provider: appearance is owned by the shared pre-paint runtime. */
export const ThemeProvider = ({ children }: { children: ReactNode }) => <>{children}</>;
export function useTheme() {
    const appearance = useAppearance();
    return { theme: appearance.resolved, toggleTheme: () => appearance.set(appearance.resolved === 'dark' ? 'light' : 'dark') };
}
