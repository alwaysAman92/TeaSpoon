import type { NavigatorScreenParams } from "@react-navigation/native";

import type { ScanResult } from "@/types";

export type TabsParamList = {
  Dashboard: undefined;
  Scan: undefined;
  Settings: undefined;
};

export type RootStackParamList = {
  Tabs: NavigatorScreenParams<TabsParamList> | undefined;
  Result: { result: ScanResult };
  Capture: { barcode: string };
};
