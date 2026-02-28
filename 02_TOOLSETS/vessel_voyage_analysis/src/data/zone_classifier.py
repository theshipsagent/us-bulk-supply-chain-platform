"""Zone type classification for maritime events."""


class ZoneClassifier:
    """Classifies maritime zones into types (CROSS_IN, CROSS_OUT, ANCHORAGE, TERMINAL)."""

    @staticmethod
    def classify_event(zone: str, action: str) -> str:
        """
        Classify a zone and action into a zone type.

        Args:
            zone: Zone name (e.g., "SWP Cross In", "Anch Area A")
            action: Action type (Enter, Exit, Arrive, Depart)

        Returns:
            Zone type: CROSS_IN, CROSS_OUT, ANCHORAGE, TERMINAL, or UNKNOWN
        """
        zone_upper = zone.upper()

        # Cross In/Out zones
        if 'SWP CROSS' in zone_upper or 'CROSS' in zone_upper:
            if action == 'Enter':
                return 'CROSS_IN'
            elif action == 'Exit':
                return 'CROSS_OUT'
            else:
                return 'UNKNOWN'

        # Anchorage zones
        if 'ANCH' in zone_upper or 'ANCHORAGE' in zone_upper:
            return 'ANCHORAGE'

        # Terminal zones (Buoys or explicit terminals)
        if 'BUOY' in zone_upper or 'TERMINAL' in zone_upper:
            return 'TERMINAL'

        # For Arrive/Depart actions without specific zone markers, assume terminal
        if action in ['Arrive', 'Depart']:
            return 'TERMINAL'

        return 'UNKNOWN'
