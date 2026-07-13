#include <iostream>

struct Celule
{
    double valeur;
    Celule* Up;
    Celule* Down;
    Celule* Left;
    Celule* Right;
};
Celule* createCelule(double val)
{
    Celule* newCelule = new Celule;
    newCelule->valeur = val;
    newCelule->Up = nullptr;
    newCelule->Down = nullptr;
    newCelule->Left = nullptr;
    newCelule->Right = nullptr;
    return newCelule;
}

int main()
{
    Celule* liste = nullptr;
    


   

    return 0;
}
