import axios from 'axios';

export interface Location {
    id: string;
    name: string;
    zipcode: string;
    canton: string;
}

export class LocationService {
    private static API_URL = 'https://api.post.ch/ZIP';
    private static cache = new Map<string, Location[]>();

    static async searchLocations(query: string): Promise<Location[]> {
        const cleanQuery = query.trim();
        
        if (this.cache.has(cleanQuery)) {
            return this.cache.get(cleanQuery)!;
        }

        try {
            const isNPA = /^\d+$/.test(cleanQuery);
            
            const response = await axios.get('https://api.swisspost.ch/locations/v1/localities/search', {
                params: {
                    q: cleanQuery,
                    limit: 10,
                    type: isNPA ? 'zip' : 'locality',
                    language: 'fr'
                },
                headers: {
                    'Accept': 'application/json',
                    'Accept-Language': 'fr'
                }
            });

            if (!response.data?.localities) {
                return [];
            }

            const locations = response.data.localities
                .filter((loc: any) => loc.zip && loc.name)
                .map((loc: any) => ({
                    id: `${loc.zip}-${loc.name}`,
                    name: loc.name,
                    zipcode: loc.zip,
                    canton: loc.canton
                }));

            this.cache.set(cleanQuery, locations);
            return locations;
        } catch (error) {
            console.error('Erreur de recherche:', error);
            return [];
        }
    }
}
