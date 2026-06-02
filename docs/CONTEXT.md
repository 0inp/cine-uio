# Cine UIO Domain Glossary

## Entities

### CinemaCompany
- **name**: String (e.g., "Multicines", "Supercines")
- **base_url**: String (e.g., "https://www.multicines.com.ec/")

### CinemaComplex
- **name**: String (e.g., "CCI", "San Luis")
- **url_part**: String (e.g., "cartelera/quito/san-luis/216")

### Movie
- **title**: String

### Screening
- **datetime**: DateTime
- **format**: String (e.g., "2D", "3D")
- **language**: String (e.g., "original + subbed in Spanish", "dubbed in Spanish")

## Relationships
- A **CinemaCompany** has many **CinemaComplexes**.
- A **CinemaComplex** has many **Screenings**.
- A **Movie** has many **Screenings**.