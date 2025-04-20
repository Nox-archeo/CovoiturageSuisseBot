<template>
  <div class="location-search">
    <div class="search-container">
      <input
        v-model="searchQuery"
        @input="handleInput"
        @focus="showHelp = true"
        type="text"
        :placeholder="'Entrez un NPA ou nom de ville'"
        class="search-input"
      />
      <div v-if="showHelp" class="search-hint">
        Tapez un NPA (ex: 1700) ou un nom de ville (ex: Fribourg)
      </div>
    </div>

    <div v-if="isSearching" class="search-status">
      Recherche en cours...
    </div>

    <ul v-if="showResults && searchResults.length > 0" class="results-list">
      <li
        v-for="location in searchResults"
        :key="location.id"
        @click="selectLocation(location)"
        class="result-item"
      >
        <div class="result-main">{{ location.name }}</div>
        <div class="result-npa">NPA: {{ location.zipcode }}</div>
      </li>
    </ul>

    <div v-if="showResults && searchResults.length === 0" class="no-results">
      Aucun résultat trouvé pour "{{ searchQuery }}"
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import { LocationService, Location } from '@/services/LocationService';
import debounce from 'lodash/debounce';

export default defineComponent({
  name: 'LocationSearch',
  props: {
    placeholder: {
      type: String,
      required: false
    }
  },
  setup(props, { emit }) {
    const searchQuery = ref('');
    const searchResults = ref<Location[]>([]);
    const showResults = ref(false);
    const isSearching = ref(false);
    const showHelp = ref(false);

    const debouncedSearch = debounce(async (query: string) => {
      if (!query.trim()) {
        searchResults.value = [];
        showResults.value = false;
        return;
      }

      isSearching.value = true;
      showResults.value = true;
      
      try {
        const results = await LocationService.searchLocations(query);
        searchResults.value = results;
      } catch (error) {
        console.error('Erreur:', error);
        searchResults.value = [];
      } finally {
        isSearching.value = false;
      }
    }, 300);

    const handleInput = () => {
      debouncedSearch(searchQuery.value);
    };

    const selectLocation = (location: Location) => {
      emit('location-selected', location);
      searchQuery.value = location.name;
      showResults.value = false;
    };

    return {
      searchQuery,
      searchResults,
      showResults,
      isSearching,
      showHelp,
      handleInput,
      selectLocation,
    };
  },
});
</script>

<style scoped>
.location-search {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.search-container {
  margin-bottom: 10px;
}

.search-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.search-hint {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff9c4;
  padding: 8px;
  border-radius: 4px;
  margin-top: 4px;
  font-size: 0.9em;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
}

.results-list {
  position: absolute;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #ccc;
  border-top: none;
  border-radius: 0 0 4px 4px;
  z-index: 1000;
}

.result-item {
  padding: 8px;
  cursor: pointer;
}

.result-item:hover {
  background-color: #f5f5f5;
}

.result-main {
  font-weight: bold;
}

.result-npa {
  color: #666;
  font-size: 0.9em;
}

.search-status {
  padding: 8px;
  color: #666;
  font-size: 0.9em;
  text-align: center;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid #ccc;
  border-top-color: #333;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

.no-results {
  padding: 8px;
  color: #666;
  font-style: italic;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
