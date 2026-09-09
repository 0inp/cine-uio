interface CityPickerProps {
  cities: string[];
  city: string;
  onSelect: (city: string) => void;
}

/** Hidden when there is nothing to choose between. */
export function CityPicker({ cities, city, onSelect }: CityPickerProps) {
  if (cities.length <= 1) return null;

  return (
    <div className="city-picker">
      <label htmlFor="city">Ciudad</label>
      <select id="city" value={city} onChange={(e) => onSelect(e.target.value)}>
        {cities.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </div>
  );
}
