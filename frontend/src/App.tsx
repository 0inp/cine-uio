import { useState, useEffect } from "react"
import "./App.css"

interface Screening {
	id: string
	time: string
	format: string
	language: string
}

interface Movie {
	id: string
	title: string
	screenings: Screening[]
}

interface CinemaComplex {
	id: string
	name: string
	movies: Movie[]
}

interface ApiResponse {
	cinemaComplexes: CinemaComplex[]
}

function App() {
	const [data, setData] = useState<ApiResponse | null>(null)
	const [loading, setLoading] = useState<boolean>(true)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		const fetchMovies = async () => {
			try {
				const response = await fetch("http://localhost:8000/api/movies")
				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`)
				}
				const result: ApiResponse = await response.json()
				setData(result)
			} catch (err) {
				setError(err instanceof Error ? err.message : "An unknown error occurred")
			} finally {
				setLoading(false)
			}
		}

		fetchMovies()
	}, [])

	if (loading) return <div className="loading">Loading...</div>
	if (error) return <div className="error">Error: {error}</div>
	if (!data) return <div className="no-data">No data available</div>

  const renderScreenings = (screenings: Screening[]) => {
    return screenings.map((screening) => (
      <div key={`${screening.datetime}-${screening.format}`} className="screening-item">
        <span className="screening-time">
          {new Date(screening.datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        <span className="screening-format">{screening.format}</span>
        <span className="screening-language">{screening.language}</span>
      </div>
    ));
  };

  return (
    <div className="app">
      <h1 className="title">Cine UIO</h1>
      {Object.entries(data).map(([movieTitle, complexes]) => {
        // Group all screenings by cinema complex
        const allScreenings = Object.entries(complexes).map(([complexName, complexData]) => ({
          complexName,
          cinemaCompany: complexData.cinema_company,
          screenings: complexData.screenings,
        }));
        
        return (
          <div key={movieTitle} className="movie-card">
            <h2 className="movie-title">{movieTitle}</h2>
            {allScreenings.map((complex) => (
              <div key={`${movieTitle}-${complex.complexName}`} className="complex-section">
                <h3 className="complex-name">
                  {complex.complexName} ({complex.cinemaCompany})
                </h3>
                <div className="screenings-list">
                  {renderScreenings(complex.screenings)}
                </div>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

export default App
