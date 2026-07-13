export interface Animal {
  id: string;
  name: string;
  type: string;
  color: string;
  description: string;
  birthYear: number;
  image: string;
  habitat: string;
  diet: string;
  size: string;
  weight: string;
}

export const animals: Animal[] = [
  {
    id: "1",
    name: "Simba",
    type: "Lion",
    color: "Golden",
    description: "Simba is a majestic African lion with a magnificent golden mane. He is the king of our savanna exhibit and loves to bask in the sun.",
    birthYear: 2018,
    image: "/lion.jpg",
    habitat: "African Savanna",
    diet: "Carnivore",
    size: "Large",
    weight: "190 kg"
  },
  {
    id: "2",
    name: "Ella",
    type: "Elephant",
    color: "Gray",
    description: "Ella is our gentle giant, an African elephant known for her intelligence and strong family bonds. She loves playing with water and mud.",
    birthYear: 2015,
    image: "/majestic-african-elephant.png",
    habitat: "African Grasslands",
    diet: "Herbivore",
    size: "Very Large",
    weight: "4000 kg"
  },
  {
    id: "3",
    name: "Zara",
    type: "Zebra",
    color: "Black and White",
    description: "Zara is a beautiful zebra with striking black and white stripes. Each zebra's pattern is unique, just like a fingerprint!",
    birthYear: 2019,
    image: "/zebra.png",
    habitat: "African Plains",
    diet: "Herbivore",
    size: "Medium",
    weight: "300 kg"
  },
  {
    id: "4",
    name: "Gerry",
    type: "Giraffe",
    color: "Yellow with Brown Spots",
    description: "Gerry is our tallest resident, reaching heights of over 5 meters. His long neck helps him reach the highest leaves on trees.",
    birthYear: 2017,
    image: "/giraffe-standing.png",
    habitat: "African Savanna",
    diet: "Herbivore",
    size: "Very Large",
    weight: "1200 kg"
  },
  {
    id: "5",
    name: "Charlie",
    type: "Crocodile",
    color: "Green",
    description: "Charlie is a Nile crocodile, one of the largest reptiles in the world. He spends most of his time in the water, waiting for the perfect moment to strike.",
    birthYear: 2012,
    image: "/crocodile.jpg",
    habitat: "African Rivers",
    diet: "Carnivore",
    size: "Large",
    weight: "500 kg"
  },
  {
    id: "6",
    name: "Polly",
    type: "Parrot",
    color: "Colorful",
    description: "Polly is a vibrant macaw with brilliant red, blue, and yellow feathers. She can mimic human speech and loves to interact with visitors.",
    birthYear: 2020,
    image: "/colorful-parrot.png",
    habitat: "Tropical Rainforest",
    diet: "Omnivore",
    size: "Small",
    weight: "1.2 kg"
  },
  {
    id: "7",
    name: "Sly",
    type: "Snake",
    color: "Green",
    description: "Sly is a green tree python, perfectly adapted to life in the trees. His bright green color helps him blend in with the forest canopy.",
    birthYear: 2021,
    image: "/snake.jpg",
    habitat: "Tropical Rainforest",
    diet: "Carnivore",
    size: "Medium",
    weight: "2 kg"
  },
  {
    id: "8",
    name: "Sally",
    type: "Salamander",
    color: "Orange",
    description: "Sally is a fire salamander with bright orange and black markings. She's nocturnal and loves cool, damp environments.",
    birthYear: 2022,
    image: "/salamander.jpg",
    habitat: "Temperate Forests",
    diet: "Carnivore",
    size: "Small",
    weight: "0.1 kg"
  },
  {
    id: "9",
    name: "Froggy",
    type: "Frog",
    color: "Green",
    description: "Froggy is a green tree frog who loves to sit on lily pads. His bright green color helps him camouflage among the leaves.",
    birthYear: 2021,
    image: "/green-frog-on-lilypad.png",
    habitat: "Freshwater Wetlands",
    diet: "Carnivore",
    size: "Very Small",
    weight: "0.05 kg"
  },
  {
    id: "10",
    name: "Shelly",
    type: "Sea Turtle",
    color: "Green",
    description: "Shelly is a green sea turtle who has traveled thousands of miles in the ocean. She's one of the oldest residents at our marine exhibit.",
    birthYear: 2010,
    image: "/sea-turtle-coral-reef.png",
    habitat: "Coral Reefs",
    diet: "Omnivore",
    size: "Large",
    weight: "150 kg"
  },
  {
    id: "11",
    name: "Wise",
    type: "Owl",
    color: "Brown",
    description: "Wise is a majestic barn owl with incredible night vision. He can rotate his head almost 270 degrees and flies silently through the night.",
    birthYear: 2019,
    image: "/majestic-owl.png",
    habitat: "Temperate Forests",
    diet: "Carnivore",
    size: "Medium",
    weight: "0.5 kg"
  },
  {
    id: "12",
    name: "Eagle",
    type: "Eagle",
    color: "Brown and White",
    description: "Eagle is a magnificent bald eagle with a wingspan of over 2 meters. He's a symbol of freedom and strength, with incredible eyesight.",
    birthYear: 2016,
    image: "/majestic-eagle.png",
    habitat: "Mountain Regions",
    diet: "Carnivore",
    size: "Large",
    weight: "6 kg"
  }
];

export const animalTypes = [...new Set(animals.map(animal => animal.type))];
export const animalColors = [...new Set(animals.map(animal => animal.color))];
export const animalHabitats = [...new Set(animals.map(animal => animal.habitat))];
