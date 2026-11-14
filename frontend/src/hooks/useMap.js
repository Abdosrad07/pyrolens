/**
 * useMap — hook pour manipuler la carte Leaflet depuis React.
 *
 * Retourne une MapHandle : mapRef + helpers flyTo/invalidateSize/getCenter.
 * Le mapRef doit être passé en prop à MapView pour recevoir la carte native.
 */

import { useRef, useCallback } from "react";
import { VIEWS } from "../data/constants.js";

export default function useMap() {
  const mapRef = useRef(null);

  const flyToView = useCallback((name) => {
    const v = VIEWS[name];
    if (!v || !mapRef.current) return;
    mapRef.current.flyTo(v.center, v.zoom, { duration: 1.4 });
  }, []);

  const flyToCoords = useCallback((lat, lng, zoom = 8) => {
    if (!mapRef.current) return;
    mapRef.current.flyTo([lat, lng], zoom, { duration: 1.2 });
  }, []);

  const invalidateSize = useCallback(() => {
    setTimeout(() => mapRef.current?.invalidateSize(), 80);
  }, []);

  const getCenter = useCallback(() => {
    const c = mapRef.current?.getCenter();
    return c ? { lat: +c.lat.toFixed(3), lng: +c.lng.toFixed(3) } : null;
  }, []);

  const getBounds = useCallback(() => {
    return mapRef.current?.getBounds() || null;
  }, []);

  return {
    mapRef,
    flyToView,
    flyToCoords,
    invalidateSize,
    getCenter,
    getBounds,
  };
}
