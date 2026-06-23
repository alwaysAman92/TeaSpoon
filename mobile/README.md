# TeaSpoon Mobile

React Native (Expo, TypeScript). The daily loop: Scan → Result → Dashboard, plus
a single flat Settings screen.

## Run

```bash
npm install
npx expo start
```

Then press `i` (iOS simulator), `a` (Android emulator), or scan the QR code with
the **Expo Go** app on your phone.

### Pointing at the backend

The app reads `extra.apiBaseUrl` from `app.json` (default `http://localhost:8000`).

- iOS simulator: `localhost` works as-is.
- Android emulator: use `http://10.0.2.2:8000`.
- Physical device: set your machine's LAN IP, e.g.

  ```bash
  EXPO_PUBLIC_API_BASE_URL=http://192.168.1.20:8000 npx expo start
  ```

## Structure

```
App.tsx                     # navigation shell + custom tab bar (big scan button)
src/
  theme.ts                  # design tokens (PRD Section 7)
  api/client.ts             # typed fetch client; user id in secure store
  types.ts                  # mirrors the backend schemas
  store/AppContext.tsx      # settings cache
  components/               # Stars, ProgressBar, Chip, AltCard, DetailLayer
  screens/
    ScanScreen.tsx          # F1 full-screen camera + manual entry
    ResultScreen.tsx        # F2/F5 hero stat + swipeable alts + F6-F9 details
    DashboardScreen.tsx     # F4 hero stat, bar, secondary cards, 7-day trend
    SettingsScreen.tsx      # flat settings (priority toggle, health profile)
```

## Notes

- Barcode scanning uses `expo-camera`'s `CameraView` (EAN-13/EAN-8/UPC). The PRD
  references `react-native-vision-camera + ML Kit`; `expo-camera` gives the same
  on-device scan with a far simpler Expo-managed setup.
- The `@/*` import alias is resolved by Expo's Metro (`tsconfigPaths`).
- Session id is kept in `expo-secure-store`, never `AsyncStorage`.
```
