"use client"

import { useState, useMemo } from 'react'
import { animals, Animal, animalTypes, animalColors, animalHabitats } from '../lib/animals'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Search, Filter, Info, Menu, X, Heart, MapPin, Calendar } from 'lucide-react'
import Image from 'next/image'

export default function ZooPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('')
  const [selectedColor, setSelectedColor] = useState('')
  const [selectedHabitat, setSelectedHabitat] = useState('')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [favorites, setFavorites] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const filteredAnimals = useMemo(() => {
    return animals.filter(animal => {
      const matchesSearch = animal.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          animal.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          animal.description.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesType = !selectedType || animal.type === selectedType
      const matchesColor = !selectedColor || animal.color === selectedColor
      const matchesHabitat = !selectedHabitat || animal.habitat === selectedHabitat

      return matchesSearch && matchesType && matchesColor && matchesHabitat
    })
  }, [searchTerm, selectedType, selectedColor, selectedHabitat])

  const showAnimalDetails = (animal: Animal) => {
    const details = `
🦁 ${animal.name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Type: ${animal.type}
🎨 Couleur: ${animal.color}
📅 Année de naissance: ${animal.birthYear}
🌍 Habitat: ${animal.habitat}
🍽️ Régime alimentaire: ${animal.diet}
📏 Taille: ${animal.size}
⚖️ Poids: ${animal.weight}

📝 Description:
${animal.description}
    `
    alert(details)
  }

  const toggleFavorite = (animalId: string) => {
    setFavorites(prev => 
      prev.includes(animalId) 
        ? prev.filter(id => id !== animalId)
        : [...prev, animalId]
    )
  }

  const clearFilters = () => {
    setSearchTerm('')
    setSelectedType('')
    setSelectedColor('')
    setSelectedHabitat('')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-4 border-green-500">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-xl">Z</span>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-800">Zoo Électronique</h1>
                <p className="text-gray-600">Découvrez nos animaux fascinants</p>
              </div>
            </div>
            <nav className="hidden md:flex space-x-6">
              <a href="#animals" className="text-gray-700 hover:text-green-600 font-medium">Animaux</a>
              <a href="#about" className="text-gray-700 hover:text-green-600 font-medium">À propos</a>
              <a href="#contact" className="text-gray-700 hover:text-green-600 font-medium">Contact</a>
            </nav>
            
            {/* Menu mobile */}
            <button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Menu mobile"
            >
              {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
        
        {/* Menu mobile déroulant */}
        {isMobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-gray-200 px-4 py-4">
            <nav className="flex flex-col space-y-3">
              <a href="#animals" className="text-gray-700 hover:text-green-600 font-medium py-2">Animaux</a>
              <a href="#about" className="text-gray-700 hover:text-green-600 font-medium py-2">À propos</a>
              <a href="#contact" className="text-gray-700 hover:text-green-600 font-medium py-2">Contact</a>
            </nav>
          </div>
        )}
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Filtres et recherche */}
          <aside className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6 sticky top-8">
              <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
                <Filter className="w-5 h-5 mr-2 text-green-600" />
                Filtres et Recherche
              </h2>
              
              {/* Recherche */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rechercher
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    type="text"
                    placeholder="Nom, type ou description..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Filtre par type */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type d'animal
                </label>
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger>
                    <SelectValue placeholder="Tous les types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Tous les types</SelectItem>
                    {animalTypes.map(type => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Filtre par couleur */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Couleur
                </label>
                <Select value={selectedColor} onValueChange={setSelectedColor}>
                  <SelectTrigger>
                    <SelectValue placeholder="Toutes les couleurs" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Toutes les couleurs</SelectItem>
                    {animalColors.map(color => (
                      <SelectItem key={color} value={color}>{color}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Filtre par habitat */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Habitat
                </label>
                <Select value={selectedHabitat} onValueChange={setSelectedHabitat}>
                  <SelectTrigger>
                    <SelectValue placeholder="Tous les habitats" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Tous les habitats</SelectItem>
                    {animalHabitats.map(habitat => (
                      <SelectItem key={habitat} value={habitat}>{habitat}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Bouton pour effacer les filtres */}
              <Button 
                onClick={clearFilters} 
                variant="outline" 
                className="w-full"
              >
                Effacer les filtres
              </Button>

              {/* Résultats */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">
                  <span className="font-semibold">{filteredAnimals.length}</span> animal(s) trouvé(s)
                </p>
                {favorites.length > 0 && (
                  <p className="text-sm text-red-500 mt-2 flex items-center">
                    <Heart className="w-4 h-4 mr-1 fill-red-500" />
                    <span className="font-semibold">{favorites.length}</span> favori(s)
                  </p>
                )}
              </div>
            </div>
          </aside>

          {/* Zone principale - Affichage des animaux */}
          <main className="lg:col-span-3">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Nos Animaux</h2>
              <p className="text-gray-600">Découvrez notre collection d'animaux du monde entier</p>
            </div>

            {/* Grille responsive des animaux */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {filteredAnimals.map((animal) => (
                <Card key={animal.id} className="bg-white shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden hover:-translate-y-2 group">
                  <div className="relative h-48 w-full overflow-hidden">
                    <Image
                      src={animal.image}
                      alt={animal.name}
                      fill
                      className="object-cover group-hover:scale-110 transition-transform duration-300"
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                    />
                    <button
                      onClick={() => toggleFavorite(animal.id)}
                      className="absolute top-3 right-3 p-2 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white transition-colors"
                      aria-label={`${favorites.includes(animal.id) ? 'Retirer des' : 'Ajouter aux'} favoris`}
                    >
                      <Heart 
                        className={`w-4 h-4 ${
                          favorites.includes(animal.id) 
                            ? 'text-red-500 fill-red-500' 
                            : 'text-gray-400 hover:text-red-500'
                        } transition-colors`} 
                      />
                    </button>
                  </div>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-gray-800">{animal.name}</CardTitle>
                    <CardDescription className="text-sm text-gray-600">
                      {animal.type} • {animal.color}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <MapPin className="w-3 h-3" />
                        <span>{animal.habitat}</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Calendar className="w-3 h-3" />
                        <span>Né en {animal.birthYear}</span>
                      </div>
                      <div className="flex gap-1 flex-wrap">
                        <Badge variant="secondary" className="text-xs">
                          {animal.diet}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {animal.size}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                      {animal.description}
                    </p>
                    <Button 
                      onClick={() => showAnimalDetails(animal)}
                      className="w-full"
                      size="sm"
                    >
                      <Info className="w-4 h-4 mr-2" />
                      Plus d'infos
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredAnimals.length === 0 && (
              <div className="text-center py-12 animate-fade-in">
                <div className="text-gray-400 mb-4">
                  <Search className="w-16 h-16 mx-auto animate-pulse" />
                </div>
                <h3 className="text-lg font-semibold text-gray-600 mb-2">Aucun animal trouvé</h3>
                <p className="text-gray-500 mb-4">Essayez de modifier vos critères de recherche</p>
                <Button 
                  onClick={clearFilters}
                  variant="outline"
                  className="mt-4"
                >
                  Effacer tous les filtres
                </Button>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gradient-to-r from-gray-800 to-gray-900 text-white py-12 mt-16">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4 text-green-400">Zoo Électronique</h3>
              <p className="text-gray-300 text-sm">
                Découvrez la beauté et la diversité de la nature à travers notre collection d'animaux fascinants du monde entier.
              </p>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-4">Navigation</h4>
              <ul className="space-y-2 text-sm text-gray-300">
                <li><a href="#animals" className="hover:text-green-400 transition-colors">Nos Animaux</a></li>
                <li><a href="#about" className="hover:text-green-400 transition-colors">À Propos</a></li>
                <li><a href="#contact" className="hover:text-green-400 transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-4">Informations</h4>
              <div className="text-sm text-gray-300 space-y-1">
                <p>📍 Parc Zoologique Électronique</p>
                <p>📞 +33 1 23 45 67 89</p>
                <p>✉️ contact@zoo-electronique.fr</p>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-8 pt-8 text-center">
            <p className="text-gray-400 text-sm">&copy; 2024 Zoo Électronique. Tous droits réservés.</p>
            <p className="text-gray-500 text-xs mt-2">Développé avec ❤️ pour l'éducation et la conservation</p>
          </div>
        </div>
      </footer>
    </div>
  )
}