export default function SearchBar({ value, onChange, loading }) {
  return (
    <div className="search-bar-wrapper">
      <div className="search-bar">
        <svg className="search-icon" viewBox="0 0 24 24" width="20" height="20">
          <path
            fill="currentColor"
            d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
          />
        </svg>
        <input
          type="text"
          placeholder="Search Pokémon..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label="Search Pokémon"
        />
        {loading && <div className="search-spinner" aria-hidden="true" />}
        {value && (
          <button
            type="button"
            className="search-clear"
            onClick={() => onChange('')}
            aria-label="Clear search"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  )
}
