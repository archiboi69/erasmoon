// Wrap all code inside an IIFE to avoid polluting the global namespace
(function () {
    // Wait for the DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function () {
      // Determine which page we're on
      const isIndexPage = document.body.classList.contains('index-page');
      const isCityDetailPage = document.body.classList.contains('city-detail-page');
  
      // Initialize common variables
      const feedbackButton = document.getElementById('feedbackButton');
      const feedbackPopup = document.getElementById('feedbackPopup');
      const feedbackForm = document.getElementById('feedbackForm');
      const popupCloseButton = document.getElementById('closeFeedback');

      // Initialize page-specific variables
      let cityCards = [];
      if (isIndexPage) {
        cityCards = Array.from(document.querySelectorAll('.city-grid__card'));
      }
  
      // Initialize functions
      const app = {
        // Common properties
        moonScoreMapping: {
            '0.0': '🌑🌑🌑🌑🌑',
            '0.5': '🌗🌑🌑🌑🌑',
            '1.0': '🌕🌑🌑🌑🌑',
            '1.5': '🌕🌗🌑🌑🌑',
            '2.0': '🌕🌕🌑🌑🌑',
            '2.5': '🌕🌕🌗🌑🌑',
            '3.0': '🌕🌕🌕🌑🌑',
            '3.5': '🌕🌕🌕🌗🌑',
            '4.0': '🌕🌕🌕🌕🌑',
            '4.5': '🌕🌕🌕🌕🌗',
            '5.0': '🌕🌕🌕🌕🌕',
          },

        // Common functions
        init: function () {
          this.setupFeedbackPopup();
          this.setupJoinWaitlist();
  
          if (isIndexPage) {
            this.initIndexPage();
          } else if (isCityDetailPage) {
            this.initCityDetailPage();
          }
        },
  
        /** ---------------- Common Functions ---------------- **/
  
        /**
         * Sets up the feedback popup functionality.
         */
        setupFeedbackPopup: function () {
          // Feedback popup event listeners
          if (feedbackButton && feedbackPopup) {
            feedbackButton.addEventListener('click', () => {
              feedbackPopup.style.display = 'block';
            });
  
            feedbackPopup.addEventListener('click', (event) => {
              if (event.target === feedbackPopup) {
                feedbackPopup.style.display = 'none';
              }
            });
          }
          
          if (popupCloseButton) {
            popupCloseButton.addEventListener('click', () => {
              feedbackPopup.style.display = 'none';
            });
          }

          // Submit feedback form
          if (feedbackForm) {
            feedbackForm.addEventListener('submit', function (e) {
              e.preventDefault();
              const feedbackText = document.getElementById('feedbackText').value;
              fetch('/submit_feedback', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ feedback: feedbackText }),
              })
                .then((response) => response.json())
                .then((data) => {
                  alert('Thank you for your feedback!');
                  feedbackPopup.style.display = 'none';
                  feedbackForm.reset();
                })
                .catch((error) => {
                  console.error('Error:', error);
                  alert('There was an error submitting your feedback. Please try again.');
                });
            });
          }
        },

        /**
         * Sets up the join waitlist functionality.
         */
        setupJoinWaitlist: function () {
          const joinButton = document.getElementById('joinButton');
          const joinPopup = document.getElementById('joinPopup');
          const closeJoin = document.getElementById('closeJoin');
          const joinForm = document.getElementById('joinForm');
          const joinMessage = document.getElementById('joinMessage');

          if (joinButton && joinPopup) {
            joinButton.addEventListener('click', () => {
              joinPopup.style.display = 'block';
            });

            joinPopup.addEventListener('click', (event) => {
              if (event.target === joinPopup) {
                joinPopup.style.display = 'none';
              }
            });
          }

          if (closeJoin) {
            closeJoin.addEventListener('click', () => {
              joinPopup.style.display = 'none';
            });
          }

          if (joinForm) {
            joinForm.addEventListener('submit', function (e) {
              e.preventDefault();
              const email = document.getElementById('emailInput').value.trim();
              
              // Basic email validation
              const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
              if (!emailRegex.test(email)) {
                joinMessage.textContent = "Please enter a valid email address.";
                joinMessage.style.color = 'red';
                return;
              }
              
              fetch('/join_waitlist', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({email: email}),
              })
              .then(response => response.json())
              .then(data => {
                if (data.success) {
                  joinMessage.textContent = "You've been added to the waitlist!";
                  joinMessage.style.color = 'var(--color-accent)';
                  joinForm.reset();
                } else {
                  joinMessage.textContent = "There was an error. Please try again.";
                  joinMessage.style.color = 'red';
                }
              })
              .catch((error) => {
                console.error('Error:', error);
                joinMessage.textContent = "There was an error. Please try again.";
                joinMessage.style.color = 'red';
              });
            });
          }
        },
  
        /** ---------------- Index Page Functions ---------------- **/
  
        /**
         * Initializes functionalities specific to the index page.
         */
        initIndexPage: function () {
          
          // Initialize variables
          this.searchInput = document.getElementById('searchInput');
          this.languageSelect = document.getElementById('languageSelect');
          this.sortSelect = document.getElementById('sortSelect');
          this.toggleFiltersButton = document.getElementById('toggleFilters');
          this.filterPopup = document.getElementById('filterPopup');
          this.closeFiltersButton = document.getElementById('closeFilters');
          this.visibleCitiesCount = document.getElementById('visibleCitiesCount');
          this.totalCitiesCount = document.getElementById('totalCitiesCount');
          this.cityCards = cityCards;
          
  
          // Initialize filters
          this.activeFilters = {
            budget: 'all',
            weather: 'all',
            population: 'all',
          };

          // Initialize last touched card
          this.lastTouchedCard = null
  
          // Initialize event listeners
          this.setupIndexPageEventListeners();
  
          // Initial setup
          this.resetFilters();
          this.resetCardStates();
          this.computeAndRenderRatings();
          this.filterCities();
        },
  
        /**
         * Sets up event listeners for the index page.
         */
        setupIndexPageEventListeners: function () {
            const searchInput = this.searchInput;
            const languageSelect = this.languageSelect;
            const sortSelect = this.sortSelect;
            const toggleFiltersButton = this.toggleFiltersButton;
            const filterPopup = this.filterPopup;
            const closeFiltersButton = this.closeFiltersButton;
            const cityCards = this.cityCards;
  
          // Search input
          if (searchInput) {
            searchInput.addEventListener('input', () => {
              this.filterCities();
            });
          }
  
          // Language select
          if (languageSelect) {
            languageSelect.addEventListener('change', () => {
              this.computeAndRenderRatings();
              this.filterCities();
            });
          }
  
          // Sort select
          if (sortSelect) {
            sortSelect.addEventListener('change', () => {
              this.filterCities();
            });
          }
  
          // Filter buttons
          const filterButtons = document.querySelectorAll('.filter-popup__button');
          if (filterButtons.length > 0) {
            filterButtons.forEach((button) => {
              button.addEventListener('click', () => {
                this.handleFilterButtonClick(button);
              });
            });
          }
  
      
          // Filter popup
          if (toggleFiltersButton && filterPopup) {
            toggleFiltersButton.addEventListener('click', () => {
              filterPopup.style.display = 'block';
            });
  
            filterPopup.addEventListener('click', (event) => {
              if (event.target === filterPopup) {
                filterPopup.style.display = 'none';
                this.updateFilterButtonState();
              }
            });
          }
  
          if (closeFiltersButton && filterPopup) {
            closeFiltersButton.addEventListener('click', () => {
              filterPopup.style.display = 'none';
              this.updateFilterButtonState();
            });
          }
  
          // Reset card states when the page becomes visible
          document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
              this.resetCardStates();
            }
          });
  
          // Reset card states when the page is loaded
          window.addEventListener('pageshow', (event) => {
            if (event.persisted) {
              this.resetCardStates();
            }
          });

          // City card events
          cityCards.forEach((card) => {
            this.setupCityCardEventListeners(card);
          });
          
          // Lazy load background images
          this.setupLazyLoading(cityCards);
        },
  
        /**
         * Handles filter button clicks.
         * @param {HTMLElement} button - The clicked filter button.
         */
        handleFilterButtonClick: function (button) {
          const filterTypeElement = button.closest('.filter-popup__section').querySelector('h3');
          if (!filterTypeElement) return;
          const filterType = filterTypeElement.textContent.toLowerCase();
          const filterValue =
            button.dataset[filterType] || button.dataset.population || button.dataset.budget || button.dataset.weather;
  
          // Remove active class from all buttons in the same filter group
          button
            .closest('.filter-popup__filter-row')
            .querySelectorAll('.filter-popup__button')
            .forEach((btn) => btn.classList.remove('filter-popup__button--active'));
  
          // Add active class to clicked button
          button.classList.add('filter-popup__button--active');
  
          // Update active filter
          if (filterType === 'budget') this.activeFilters.budget = filterValue;
          else if (filterType === 'weather') this.activeFilters.weather = filterValue;
          else if (filterType === 'size') this.activeFilters.population = filterValue;
  
          this.updateFilterButtonState();
          this.filterCities();
        },
  
        /**
         * Sets up event listeners for city cards.
         * @param {HTMLElement} card - The city card element.
         */
        setupCityCardEventListeners: function (card) {
            card.addEventListener('click', function(event) {
                const tapForDetails = card.querySelector('.city-grid__tap-for-details');
                // Check if the device does not support hover (mobile devices)
                if (window.matchMedia('(hover: none) and (pointer: coarse)').matches) {
                    // If metrics are not shown yet
                    if (!card.classList.contains('show-metrics')) {
                        event.preventDefault(); // Prevent navigation
                        card.classList.add('show-metrics'); // Show metrics
                        
                        if (tapForDetails) {
                            tapForDetails.style.display = 'block';
                        }
                    } else {
                        // Metrics are already shown, allow navigation to details
                        // Optionally, remove 'show-metrics' class after navigation
                    }
                }
            });

            // Add event listener to remove show-metrics and hide tapForDetails when clicked outside of card
            document.addEventListener('click', function(event) {
                if (!card.contains(event.target)) {
                    card.classList.remove('show-metrics');
                    const tapForDetails = card.querySelector('.city-grid__tap-for-details');
                    if (tapForDetails) {
                        tapForDetails.style.display = 'none';
                    }
                }
            });
        },
        
        /**
         * Updates the temperature range for a city card.
         * @param {HTMLElement} card - The city card element.
         */
        updateTempRange: function (card) {
            const temps = {
                min: parseInt(card.dataset.meanFebMin),
                max: parseInt(card.dataset.meanJulMax)
            };
            const tempRange = card.querySelector('.city-grid__temp-range'); // Ensure this matches your updated HTML
            tempRange.innerHTML = ''; // Clear existing bars

            if (
                temps.min !== undefined &&
                temps.max !== undefined &&
                temps.min !== '' &&
                temps.max !== '' &&
                !isNaN(temps.min) &&
                !isNaN(temps.max)
            ) {
                this.createTempBar(temps.min, temps.max, tempRange);
            }
        },

        /**
         * Updates the rating bar for a specific rating type.
         * @param {HTMLElement} card - The city card element.
         * @param {string} ratingType - The rating label (e.g., 'popularity').
         * @param {number} ratingValue - The rating value.
         */
        updateCityCardRatingBar: function (card, ratingType, ratingValue) {
            const container = card.querySelector(`.city-grid__rating--${ratingType}`);
            if (!container) return;

            const ratingBar = container.querySelector('.city-grid__rating-bar');
            const ratingFill = ratingBar.querySelector('.city-grid__rating-fill');

            if (ratingValue !== 'N/A') {
                ratingFill.style.width = `${ratingValue * 20}%`;
                ratingFill.style.display = 'block';
            } else {
                ratingFill.style.display = 'none';
            }
        },

        /**
         * Updates the ratings for all city cards based on the selected language.
         */
        computeAndRenderRatings: function () {
            const selectedLanguage = this.languageSelect.value;

            // Calculate mean and standard deviation for each metric
            const metrics = {
                erasmusPopulation: [],
                costOfLiving: [],
                safetyIndex: [],
                publicTransportSatisfaction: []
            };
    
            this.cityCards.forEach(card => {
                metrics.erasmusPopulation.push(parseFloat(card.dataset.erasmusPopulation) || 0);
                metrics.costOfLiving.push(80 - parseFloat(card.dataset.costOfLivingPlusRent) || 0);
                metrics.safetyIndex.push(parseFloat(card.dataset.safetyIndex) || 0);
                metrics.publicTransportSatisfaction.push(parseFloat(card.dataset.publicTransportSatisfaction) || 0);
            });
    
            const mean = {};
            const stdDev = {};
    
            for (const metric in metrics) {
                const values = metrics[metric];
                mean[metric] = values.reduce((a, b) => a + b, 0) / values.length;
                stdDev[metric] = Math.sqrt(values.map(x => Math.pow(x - mean[metric], 2)).reduce((a, b) => a + b) / values.length);
            }
    
            this.cityCards.forEach(card => {
                const eurostatCode = card.dataset.eurostatCode;
                const erasmusPopulation = parseFloat(card.dataset.erasmusPopulation) || 0;
                const costOfLiving = 80 - parseFloat(card.dataset.costOfLivingPlusRent) || 0;
                const safetyIndex = parseFloat(card.dataset.safetyIndex) || 0;
                const publicTransportSatisfaction = parseFloat(card.dataset.publicTransportSatisfaction) || 0;
                const languagePercentage = parseFloat(card.dataset[`lang-${selectedLanguage.toLowerCase()}`]) || 0;
    
                const languageLabel = card.querySelector('.city-grid__language-label');
    
    
                // Calculate z-scores
                const zScores = {
                    popularity: (erasmusPopulation - mean.erasmusPopulation) / stdDev.erasmusPopulation,
                    cost: (costOfLiving - mean.costOfLiving) / stdDev.costOfLiving,
                    safety: (safetyIndex - mean.safetyIndex) / stdDev.safetyIndex,
                    publicTransport: (publicTransportSatisfaction - mean.publicTransportSatisfaction) / stdDev.publicTransportSatisfaction,
                };
    
                // Normalize z-scores to a 0-5 scale
                const normalize = z => Math.min(Math.max((z + 3) / 6 * 5, 0), 5); // Assuming z-scores are within -3 to +3
    
                const popularityScore = normalize(zScores.popularity);
                const costScore = ((100 - parseFloat(card.dataset.costOfLivingPlusRent)) / 75) * 5 || 0;
                const safetyScore = normalize(zScores.safety);
                const publicTransportScore = normalize(zScores.publicTransport);
                const languageScore = languagePercentage / 20; // Assuming language percentage is already a percentage
    
                this.updateCityCardRatingBar(card, 'popularity', popularityScore);
                this.updateCityCardRatingBar(card, 'cost', costScore);
                this.updateCityCardRatingBar(card, 'safety', safetyScore);
                this.updateCityCardRatingBar(card, 'public-transport', publicTransportScore);
                this.updateCityCardRatingBar(card, 'language', languageScore);
                languageLabel.textContent = selectedLanguage
    
                const moonScore = (
                    (popularityScore * 0.2) +
                    (costScore * 0.2) +
                    (safetyScore * 0.2) +
                    (publicTransportScore * 0.2) +
                    (languageScore * 0.2)
                );
    
                const moonScoreElement = card.querySelector('.city-grid__moon-score-value');
                const moonScoreEmojiElement = card.querySelector('.city-grid__moon-score-emoji');
                
                if (moonScoreElement && moonScoreEmojiElement) {
                    if (moonScore > 0) {
                        const moonScoreRounded = moonScore.toFixed(1);
                        moonScoreElement.textContent = moonScoreRounded;
    
                        // Find the closest key in the moonScoreMapping
                        const closestKey = Object.keys(this.moonScoreMapping).reduce((prev, curr) => 
                            Math.abs(curr - moonScoreRounded) < Math.abs(prev - moonScoreRounded) ? curr : prev
                        );
                        moonScoreEmojiElement.textContent = this.moonScoreMapping[closestKey];
                    } else {
                        moonScoreElement.textContent = 'N/A';
                        moonScoreEmojiElement.textContent = '';
                    }
                }
    
                // Store the computed scores in local storage for later use
                const cityData = {
                    popularityScore,
                    costScore,
                    safetyScore,
                    publicTransportScore,
                    languageScore,
                    selectedLanguage,
                    moonScore
                };
                localStorage.setItem(`cityData-${eurostatCode}`, JSON.stringify(cityData));
            });
        },
  
        /**
         * Filters and sorts city cards based on active filters and search term.
         */
        filterCities: function () {
            const searchTerm = this.searchInput ? this.searchInput.value.toLowerCase().trim() : '';
            const sortBy = this.sortSelect.value;
            let visibleLinks = []; // Collecting .city-grid__link elements

            this.cityCards.forEach((card) => {
                const name = (card.dataset.englishName || '').toLowerCase();
                const localName = (card.dataset.localName || '').toLowerCase();
                const country = (card.dataset.englishCountry || '').toLowerCase();
                const localCountry = (card.dataset.localCountry || '').toLowerCase();
                const monthlyBudget = parseFloat(card.dataset.monthlyBudget) || Infinity;
                const weatherCategory = this.getWeatherCategory(card);
                const population = parseInt(card.dataset.population) || 0;
                
                // Filter based on search term
                const matchesSearch = searchTerm === '' || 
                                    name.includes(searchTerm) || 
                                    localName.includes(searchTerm) ||
                                    country.includes(searchTerm) ||
                                    localCountry.includes(searchTerm);
                
                // Filter based on filter popup
                const matchesBudget = this.activeFilters.budget === 'all' || 
                                    (this.activeFilters.budget === '700' && monthlyBudget <= 700) ||
                                    (this.activeFilters.budget === '850' && monthlyBudget <= 850) ||
                                    (this.activeFilters.budget === '1000' && monthlyBudget <= 1000);
                const matchesWeather = this.activeFilters.weather === 'all' || weatherCategory === this.activeFilters.weather;
                const matchesPopulation = this.activeFilters.population === 'all' || this.getPopulationCategory(population) === this.activeFilters.population;

                const link = card.closest('.city-grid__link'); // Get the parent link element

                if (matchesSearch && matchesBudget && matchesWeather && matchesPopulation) {
                    link.style.display = 'block';
                    visibleLinks.push(link);
                } else {
                    link.style.display = 'none';
                }

                this.updateTempRange(card);
            });
            this.sortVisibleCities(visibleLinks, sortBy);
        },

        /**
         * Sorts and updates the display order of visible city links.
         * @param {Array} visibleLinks - The array of visible city link elements (.city-grid__link).
         * @param {string} sortBy - The criteria to sort by ('popularity', 'cost', 'moon-score').
         */
        sortVisibleCities: function (visibleLinks, sortBy) {

            visibleLinks.sort((a, b) => {
                const aCard = a.querySelector('.city-grid__card');
                const bCard = b.querySelector('.city-grid__card');

                if (sortBy === 'popularity') {
                    const aPopularity = parseInt(aCard.dataset.erasmusPopulation) || 0;
                    const bPopularity = parseInt(bCard.dataset.erasmusPopulation) || 0;
                    return bPopularity - aPopularity; // Descending order
                } else if (sortBy === 'cost') {
                    const aCost = parseFloat(aCard.dataset.costOfLivingPlusRent) || Infinity;
                    const bCost = parseFloat(bCard.dataset.costOfLivingPlusRent) || Infinity;
                    return aCost - bCost; // Ascending order
                } else { // 'moon-score' is the default
                    const aRating = parseFloat(aCard.querySelector('.city-grid__moon-score-value').textContent) || 0;
                    const bRating = parseFloat(bCard.querySelector('.city-grid__moon-score-value').textContent) || 0;
                    return bRating - aRating; // Descending order
                }
            });

            const parentContainer = document.querySelector('.city-grid');

            // Create a Document Fragment to minimize reflows
            const fragment = document.createDocumentFragment();

            visibleLinks.forEach((link, index) => {
                // Update rank
                const card = link.querySelector('.city-grid__card');
                card.dataset.rank = index + 1;
                const rankElement = link.querySelector('.city-grid__rank');
                if (rankElement) {
                    rankElement.textContent = index + 1;
                }

                // Append the sorted link to the fragment
                fragment.appendChild(link);
            });

            // Append the fragment to the parent container, rearranging the order
            parentContainer.appendChild(fragment);

            this.updateVisibleCitiesCount(visibleLinks.length);
        },

        /**
         * Updates the visible cities count and total cities count.
         * @param {number} count - The number of visible cities.
         */
        updateVisibleCitiesCount: function (count) {
            if (this.visibleCitiesCount && this.totalCitiesCount) {
                this.visibleCitiesCount.textContent = count;
                this.totalCitiesCount.textContent = this.cityCards.length;
            }
        },
        
        /**
         * Resets all filters to their default state.
         */
        resetFilters: function () {
          this.activeFilters = {
            budget: 'all',
            weather: 'all',
            population: 'all',
          };
  
          const filterButtons = document.querySelectorAll('.filter-popup__button');
          if (filterButtons.length > 0) {
            filterButtons.forEach((button) => {
              if (
                button.dataset.population === 'all' ||
                button.dataset.budget === 'all' ||
                button.dataset.weather === 'all'
              ) {
                button.classList.add('filter-popup__button--active');
              } else {
                button.classList.remove('filter-popup__button--active');
              }
            });
          }

          this.updateFilterButtonState();
          this.filterCities();
        },
  
        /**
         * Updates the state of the filter toggle button.
         */
        updateFilterButtonState: function () {
          if (!this.toggleFiltersButton) return;
  
          const isAnyFilterActive =
            this.activeFilters.budget !== 'all' ||
            this.activeFilters.weather !== 'all' ||
            this.activeFilters.population !== 'all';
  
          if (isAnyFilterActive) {
            this.toggleFiltersButton.classList.add('search-bar__toggle-button--active');
          } else {
            this.toggleFiltersButton.classList.remove('search-bar__toggle-button--active');
          }
        },
  
        /**
         * Resets the card states to their initial state.
         */
        resetCardStates: function () {
            this.lastTouchedCard = null;
            console.log('Resetting card states');
            console.log('this.cityCards:', this.cityCards);
            this.cityCards.forEach((card) => {
                card.classList.remove('show-metrics');
                const tapForDetails = card.querySelector('.city-grid__tap-for-details');
                if (tapForDetails) tapForDetails.style.display = 'none';
            });
        },
        
        /**
         * Sets up lazy loading for city card images.
         * @param {Array} cityCards - An array of city card elements.
         */
        setupLazyLoading: function (cityCards) {
            const lazyLoadObserver = new IntersectionObserver((entries, observer) => {
              entries.forEach((entry) => {
                if (entry.isIntersecting) {
                  const card = entry.target;
                  card.style.backgroundImage = `url('${card.dataset.backgroundImage}')`;
                  observer.unobserve(card);
                }
              });
            });
    
            cityCards.forEach((card) => {
              lazyLoadObserver.observe(card);
            });
        },

        /** ---------------- City Detail Page Functions ---------------- **/

        /**
         * Initializes functionalities specific to the city detail page.
         */
        initCityDetailPage: function () {
          
          // Get city data from script tag
          const cityDataScript = document.getElementById('city-data');
          if (cityDataScript) {
            try {
              const cityData = JSON.parse(cityDataScript.textContent);
              this.cityCoordinates = cityData.cityCoordinates;
              this.universities = cityData.universities;
            } catch (error) {
              console.error('Error parsing city data:', error);
              return;
            }
          } else {
            console.error('City data script tag not found.');
            return;
          }
          
          // Initialize variables
          this.weatherDetail = document.getElementById('weatherDetail');
          
          const cityId = window.location.pathname.split('/').pop(); 
          this.loadAndRenderRatings(cityId);
          this.renderMonthlyWeather();
  
          // Read more button
          const readMoreBtn = document.getElementById('readMoreBtn');
          if (readMoreBtn) {
            readMoreBtn.addEventListener('click', () => {
              const guideFull = document.getElementById('guideFull');
              const guidePreview = document.getElementById('guidePreview');
              if (guideFull && guidePreview) {
                if (guideFull.style.display === 'none') {
                  guideFull.style.display = 'block';
                  guidePreview.style.display = 'none';
                  readMoreBtn.textContent = 'Read less';
                } else {
                  guideFull.style.display = 'none';
                  guidePreview.style.display = 'block';
                  readMoreBtn.textContent = 'Read more';
                }
              }
            });
          }
  
          // Initialize elements
          this.initTabs();
          this.initializeUniversityMap();
          this.createBudgetPieChart();
        },

        initTabs: function() {
            const tabLinks = document.querySelectorAll('.tabs__link');
            
            tabLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    // Remove active class from all tabs
                    tabLinks.forEach(tab => tab.classList.remove('tabs__link--active'));
                    
                    // Add active class to clicked tab
                    link.classList.add('tabs__link--active');
                    
                    // Show corresponding content
                    const targetId = link.getAttribute('href').substring(1);
                    this.showContent(targetId);
                });
            });

            // Set the first tab as active by default
            if (tabLinks.length > 0) {
                tabLinks[0].click();
            }
        },

        showContent: function(targetId) {
            // Hide all content sections except hero
            document.querySelectorAll('section').forEach(section => {
                if (section.id !== 'hero') {
                    section.style.display = 'none';
                }
            });

            // Show the target content section
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.style.display = 'block';
            }
        },

        /**
         * Retrieves city data from local storage and updates the rating bars.
         * @param {string} cityId - The ID of the city.
         */
        loadAndRenderRatings: function (cityId) {
            const cityData = JSON.parse(localStorage.getItem(`cityData-${cityId}`));
            const selectedLanguage = cityData.selectedLanguage;
            if (cityData) {
                this.updateDetailRatingBar('popularity', cityData.popularityScore);
                this.updateDetailRatingBar('cost', cityData.costScore);
                this.updateDetailRatingBar('safety', cityData.safetyScore);
                this.updateDetailRatingBar('public-transport', cityData.publicTransportScore);
                this.updateDetailRatingBar('language', cityData.languageScore);
    
                // Update the language label
                const languageLabel = document.getElementById('languageLabel');
                if (languageLabel) {
                    languageLabel.textContent = selectedLanguage;
                } else {
                    console.warn(`No language label found for city ${cityId}`);
                }
    
                const moonScoreElement = document.getElementById('moonScoreValue');
                const moonScoreEmojiElement = document.querySelector('.rating__emoji'); // Direct selection
    
                if (moonScoreElement && moonScoreEmojiElement) {
                    if (cityData.moonScore > 0) {
                        const moonScoreRounded = parseFloat(cityData.moonScore.toFixed(1));
                        moonScoreElement.textContent = moonScoreRounded;
    
                        // Find the closest key in the moonScoreMapping
                        const closestKey = Object.keys(this.moonScoreMapping).reduce((prev, curr) => {
                            return Math.abs(parseFloat(curr) - moonScoreRounded) < Math.abs(parseFloat(prev) - moonScoreRounded) ? curr : prev;
                        });
    
                        moonScoreEmojiElement.textContent = this.moonScoreMapping[closestKey] || "🌑🌑🌑🌑🌑";
                    } else {
                        moonScoreElement.textContent = 'N/A';
                        moonScoreEmojiElement.textContent = '';
                    }
                }
            } else {
                console.warn(`No data found in localStorage for key: cityData-${cityId}`);
            }
        },
        
        /**
         * Updates the rating bar detail for a specific rating type.
         * @param {string} type - The rating type (e.g., 'popularity').
         * @param {number} score - The rating score.
         */
        updateDetailRatingBar: function (type, score) {
            const ratingContainer = document.querySelector(`.rating.rating--${type}`);
            if (ratingContainer) {
                const ratingFill = ratingContainer.querySelector('.rating__fill');
                const ratingValue = ratingContainer.querySelector('.rating__value');

                if (score) {
                    ratingFill.style.width = `${score * 20}%`;
                    ratingValue.textContent = score.toFixed(1);
                } else {
                    ratingFill.style.width = '0%';
                    ratingValue.textContent = '0.0';
                }
            } else {
                console.warn(`Rating container for type "${type}" not found.`);
            }
        },

        /**
         * Updates the weather detail for the city.
         */
        renderMonthlyWeather: function () {
            if (!this.weatherDetail) {
                console.error('Weather detail element not found');
                return;
            }
           
            const months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'];
    
            months.forEach((month) => {
                const min = parseInt(this.weatherDetail.dataset[`mean-${month}-min`]);
                const max = parseInt(this.weatherDetail.dataset[`mean-${month}-max`]);
                            
                const tempRangeElement = document.getElementById(month);
                if (tempRangeElement) {
                    if (!isNaN(min) && !isNaN(max)) {
                        console.log('Attempting to create temp bar')
                        this.createTempBar(min, max, tempRangeElement);
                    } else {
                        console.log(`No valid data for ${month}`);
                    }
                } else {
                    console.warn(`Element for month "${month}" not found.`);
                }
            });
        },
  
  
        /**
         * Creates the budget pie chart.
         */
        createBudgetPieChart: function () {
            const totalBudgetElement = document.getElementById('totalBudget');
            const rentBudgetElement = document.getElementById('rentBudget');
            const groceriesBudgetElement = document.getElementById('groceriesBudget');
            const transportBudgetElement = document.getElementById('transportBudget');

            if (totalBudgetElement && rentBudgetElement && groceriesBudgetElement && transportBudgetElement) {
                const totalBudget = parseInt(totalBudgetElement.textContent);
                const rentBudget = parseInt(rentBudgetElement.textContent) || 0;
                const groceriesBudget = parseInt(groceriesBudgetElement.textContent) || 0;
                const transportBudget = parseInt(transportBudgetElement.textContent) || 0;
                const otherBudget = totalBudget - rentBudget - groceriesBudget - transportBudget;
                
                const ctx = document.getElementById('budgetPieChart').getContext('2d');
                new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: [' Rent', ' Groceries', ' Transport', ' Fun!'],
                        datasets: [{
                            data: [rentBudget, groceriesBudget, transportBudget, otherBudget],
                            backgroundColor: [
                                '#3D46F2',
                                '#636AF2',
                                '#8D92F2',
                                '#F2AE30'
                            ],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    font: {
                                        size: 12
                                    },
                                    padding: 20 // Add padding to move the legend lower
                                }
                            },
                            title: {
                                display: false,
                            }
                        }
                    }
                });
            } else {
                console.warn('Budget elements not found. Pie chart cannot be created.');
            }
        },
  
        /**
         * Initializes the map for universities.
         */
        initializeUniversityMap: function () {
            if (this.cityCoordinates.lat !== null && this.cityCoordinates.lon !== null) {
                var map = L.map('map').setView([this.cityCoordinates.lat, this.cityCoordinates.lon], 11);
    
                // Add OpenStreetMap tile layer
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);
    
                // Loop through the university data and add markers to the map
                this.universities.forEach(function(uni) {
                    if (uni.lat !== null && uni.lon !== null) {
                        var marker = L.marker([uni.lat, uni.lon], {
                            icon: L.divIcon({
                                className: 'university-marker',
                                html: `<div class="university-marker__emoji">🌕</div><div class="university-marker__number">${uni.index}</div>`,
                                iconSize: [25, 25]
                            })
                        }).addTo(map);
                        marker.bindPopup('<b>' + uni.name + '</b><br><a href="' + uni.url + '" target="_blank">Visit Website</a>');
                    }
                });
            } else {
                console.warn('City coordinates are not available. Map cannot be initialized.');
                document.getElementById('map').innerHTML = '<p>Map data not available for this city.</p>';
            }
        },

        /** ---------------- Utility Functions ---------------- **/
        

        /**
         * Creates a temperature bar element with a gradient based on the temperature range.
         * @param {number} low - The low temperature.
         * @param {number} high - The high temperature.
         * @param {HTMLElement} tempRange - The container element for the temperature range.
         */
        createTempBar: function (low, high, tempRange) {
            const TEMP_RANGE = { MIN: -11, MAX: 36 };
            const COLOR_STOPS = [
                [94, 79, 162], [50, 136, 189], [102, 194, 165], [171, 221, 164], [230, 245, 152],
                [255, 255, 191], [254, 224, 139], [253, 174, 97], [244, 109, 67], [213, 62, 79], [158, 1, 66]
            ]; // Colors for Spectral colormap
        
            // Interpolates a color based on the temperature.
            function interpolateColor(temp) {
                const normalizedTemp = Math.max(0, Math.min((temp - TEMP_RANGE.MIN) / (TEMP_RANGE.MAX - TEMP_RANGE.MIN), 1));
                const index = normalizedTemp * (COLOR_STOPS.length - 1);
                const lowerIndex = Math.floor(index);
                const upperIndex = Math.ceil(index);
                const fraction = index - lowerIndex;
        
                if (lowerIndex === upperIndex) return COLOR_STOPS[lowerIndex];
        
                if (!COLOR_STOPS[lowerIndex] || !COLOR_STOPS[upperIndex]) {
                    return COLOR_STOPS[0]; // Return the first color as a fallback
                }
        
                return COLOR_STOPS[lowerIndex].map((c, i) =>
                    Math.round(c + fraction * (COLOR_STOPS[upperIndex][i] - c))
                );
            }
        
            // Creates a gradient based on temperature range.
            function createGradient(low, high) {
                const steps = 10;
                return `linear-gradient(to right, ${[...Array(steps + 1)]
                    .map((_, i) => {
                        const temp = low + (high - low) * (i / steps);
                        const color = interpolateColor(temp);
                        return `rgb(${color.join(',')}) ${(i / steps) * 100}%`;
                    })
                    .join(', ')})`;
            }
        
            const bar = document.createElement('div');
            bar.className = `temp-bar`;
            console.log('Created temp-bar div')
        
            const totalRange = TEMP_RANGE.MAX - TEMP_RANGE.MIN;
            const rangeWidth = ((high - low) / totalRange) * 100;
            const offsetLeft = ((low - TEMP_RANGE.MIN) / totalRange) * 100;
        
            Object.assign(bar.style, {
                width: `${rangeWidth}%`,
                left: `${offsetLeft}%`,
                background: createGradient(low, high),
                position: 'absolute',
            });
        
            ['low', 'high'].forEach(type => {
                const label = document.createElement('span');
                label.className = `temp-bar__label temp-bar__label--${type}`; // Updated to BEM
                label.textContent = `${type === 'low' ? low : high}°`;
                bar.appendChild(label);
            });
        
            tempRange.innerHTML = ''; // Clear existing content
            tempRange.appendChild(bar);
        },
  
        
        /**
         * Determines the weather category for a city card,
         * @param {HTMLElement} card - The city card element.
         * @returns {string} - The weather category ('cold', 'mild', 'warm').
         */
        getWeatherCategory: function (card) {
            const winterLow = parseFloat(card.dataset.meanFebMin);
        
            if (winterLow < 0) return 'cold';
            if (winterLow > 5) return 'warm';
            return 'mild';
        },
        
        /**
         * Determines the population category for a city card.
         * @param {number} population - The population of the city.
         * @returns {string} - The population category ('190000', '340000', '830000', 'metropolis').
         */
        getPopulationCategory: function (population) {
            if (population < 190000) return '190000';
            if (population < 340000) return '340000';
            if (population < 830000) return '830000';
            return 'metropolis';
        },

        // Additional utility functions can be added here as needed
      };
  
      // Start the application
      app.init();
    });
  })();