import numpy as np
import math
from pylab import *


#physical parameters
e = 1.0
me = 1.0
c = 1.0

#pick one operating mode
zeroD = False
oneD = False
twoD = False
threeD = False


#grid dimensions
Nx = 1
Ny = 1
Nz = 1

Nx_wrap = False
Ny_wrap = False
Nz_wrap = False


grid_xmin=0.0
grid_xmax=1.0

grid_ymin=0.0
grid_ymax=1.0

grid_zmin=0.0
grid_zmax=1.0
Np = 0 #total number of particles


#derived values
xgrid = np.linspace(grid_xmin, grid_xmax, Nx+1)
ygrid = np.linspace(grid_ymin, grid_ymax, Ny+1)
zgrid = np.linspace(grid_zmin, grid_zmax, Nz+1)

Ncells = Nx*Ny*Nz

dx = diff(xgrid)[0]
dy = diff(ygrid)[0]
dz = diff(zgrid)[0]


dt = 0.0

#initialize B, E, and J fields (in global scope)
Bx = np.zeros((Nx,Ny,Nz))
By = np.zeros((Nx,Ny,Nz))
Bz = np.zeros((Nx,Ny,Nz))

Ex = np.zeros((Nx,Ny,Nz))
Ey = np.zeros((Nx,Ny,Nz))
Ez = np.zeros((Nx,Ny,Nz))

Jx = np.zeros((Nx,Ny,Nz))
Jy = np.zeros((Nx,Ny,Nz))
Jz = np.zeros((Nx,Ny,Nz))

JYx = np.zeros((Nx,Ny,Nz))
JYy = np.zeros((Nx,Ny,Nz))
JYz = np.zeros((Nx,Ny,Nz))



#create grid
mpiGrid = np.empty((Nx,Ny,Nz), dtype=np.object)

def init():

    #fix dimensionality
    global zeroD
    global oneD
    global twoD
    global threeD
    global Nx
    global Ny
    global Nz

    if zeroD:
        oneD = False
        twoD = False
        threeD = False
    elif oneD:
        twoD = False
        threeD = False
    elif twoD:
        oneD = False
        threeD = False
    elif threeD:
        oneD = False
        twoD = False


    #correct grid sizes
    if zeroD:
        Nx = 1
        Ny = 1
        Nz = 1
    if oneD:
        Ny = 1
        Nz = 1
    if twoD:
        Nz = 1

    global Ncells
    Ncells = Nx*Ny*Nz


    global xgrid
    global ygrid
    global zgrid
    xgrid = np.linspace(grid_xmin, grid_xmax, Nx+1)
    ygrid = np.linspace(grid_ymin, grid_ymax, Ny+1)
    zgrid = np.linspace(grid_zmin, grid_zmax, Nz+1)

    
    global dx
    global dy
    global dz
    dx = diff(xgrid)[0]
    dy = diff(ygrid)[0]
    dz = diff(zgrid)[0]

    global dt 
    dt = 0.99/sqrt(1.0/dx/dx + 1.0/dy/dy + 1.0/dz/dz)


    #initialize B, E, and J fields (in global scope)
    global Bx
    global By
    global Bz
    global Ex
    global Ey
    global Ez
    global Jx
    global Jy
    global Jz
    global JYx
    global JYy
    global JYz
    Bx = np.zeros((Nx,  Ny, Nz))
    By = np.zeros((Nx,  Ny, Nz))
    Bz = np.zeros((Nx,  Ny, Nz))
    
    Ex = np.zeros((Nx,  Ny, Nz))
    Ey = np.zeros((Nx,  Ny, Nz))
    Ez = np.zeros((Nx,  Ny, Nz))
    
    Jx = np.zeros((Nx,  Ny, Nz))
    Jy = np.zeros((Nx,  Ny, Nz))
    Jz = np.zeros((Nx,  Ny, Nz))
    
    JYx = np.zeros((Nx, Ny, Nz))
    JYy = np.zeros((Nx, Ny, Nz))
    JYz = np.zeros((Nx, Ny, Nz))


    #create grid
    global mpiGrid
    mpiGrid = np.empty((Nx, Ny, Nz), dtype=np.object)


    return

##################################################


class CellClass(object):
    def __init__(self):
        self.Npe = 0
        self.electrons = np.empty((0,6), dtype=float64)        



def grid_limits(i,j,k):
    xmin = xgrid[i]
    xmax = xgrid[i+1]

    ymin = ygrid[j]
    ymax = ygrid[j+1]

    zmin = zgrid[k]
    zmax = zgrid[k+1]

    return xmin,xmax,ymin,ymax,zmin,zmax

def grid_lengths(i,j,k):
    dx = xgrid[i+1]-xgrid[i]
    dy = ygrid[j+1]-ygrid[j]
    dz = zgrid[k+1]-zgrid[k]

    return dx,dy,dz


#draw samples from Maxwellian distribution using rejection sampling
def Maxwellian(vb):
    fmax = 0.5*(1.0 + exp(-2.0*vb*vb))
    vmin = -5.0*vb
    vmax =  5.0*vb
    vf = vmin + (vmax-vmin)*np.random.rand()

    f = 0.5*(exp(-(vf-vb)*(vf-vb)/2.0))

    x = fmax*np.random.rand()

    if x > f:
        return Maxwellian(vb)

    return vf



#deposit particle currents into the mesh
def deposit_current(grid):
    global e
    global me
    global me

    np1 = 0
    np2 = 0
    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                cell = grid[i,j,k]
                particles = cell.electrons
                
                #print "cell:",i,j,k, " N=", len(particles), "/", cell.Npe
                np1 += len(particles)
                np2 += cell.Npe


                xmin,xmax, ymin,ymax, zmin,zmax = grid_limits(i,j,k)
                dx,dy,dz = grid_lengths(i,j,k)

                rhop = e/(dx*dy*dz)
                q = 1.0

                x = particles[:,0]
                y = particles[:,1]
                z = particles[:,2]
                ux = particles[:,3]
                uy = particles[:,4]
                uz = particles[:,5]

                gamma = sqrt(1.0 + ux*ux + uy*uy + uz*uz)
                ux = ux*c/gamma
                uy = uy*c/gamma
                uz = uz*c/gamma

                fp = (x - xmin)/dx
                fq = (y - ymin)/dy
                fr = (z - zmin)/dz

            
                #just get current to center cell; 0th order model
                if zeroD:
                    dJx = 0.5*sum(ux)*q*rhop
                    dJy = 0.5*sum(uy)*q*rhop
                    dJz = 0.5*sum(uz)*q*rhop
                    Jx[i,j,k] += dJx
                    Jy[i,j,k] += dJy
                    Jz[i,j,k] += dJz

                #cloud-in-the-cell model
                if oneD:
                    for xdir in [0,1]:
                        wx = 1.0-fp if xdir == 0 else fp
                        ii = i+xdir
                        if ii >= Nx:
                            ii -= Nx
                        dJx = 0.5*sum(ux*wx)*q*rhop
                        dJy = 0.5*sum(uy*wx)*q*rhop
                        dJz = 0.5*sum(uz*wx)*q*rhop
                        Jx[ii,j,k] += dJx
                        Jy[ii,j,k] += dJy
                        Jz[ii,j,k] += dJz

                if twoD:
                    for xdir in [0,1]:
                        wx = 1.0-fp if xdir == 0 else fp
                        ii = i+xdir
                        if ii >= Nx:
                            ii -= Nx
                        for ydir in [0,1]:
                            wy = 1.0-fq if ydir == 0 else fq
                            jj = j+ydir
                            if jj >= Ny:
                                jj -= Ny

                            dJx = 0.5*sum(ux*wx*wy)*q*rhop
                            dJy = 0.5*sum(uy*wx*wy)*q*rhop
                            dJz = 0.5*sum(uz*wx*wy)*q*rhop
                            Jx[ii,jj,k] += dJx
                            Jy[ii,jj,k] += dJy
                            Jz[ii,jj,k] += dJz

                if threeD:
                    for xdir in [0,1]:
                        wx = 1.0-fp if xdir == 0 else fp
                        ii = i+xdir
                        if ii >= Nx:
                            ii -= Nx
                        for ydir in [0,1]:
                            wy = 1.0-fq if ydir == 0 else fq
                            jj = j+ydir
                            if jj >= Ny:
                                jj -= Ny
                            for zdir in [0,1]:
                                wz = 1.0-fr if zdir == 0 else fr
                                kk = k+zdir
                                if kk >= Nz:
                                    kk -= Nz

                                dJx = 0.5*sum(ux*wx*wy*wz)*q*rhop
                                dJy = 0.5*sum(uy*wx*wy*wz)*q*rhop
                                dJz = 0.5*sum(uz*wx*wy*wz)*q*rhop
                                Jx[ii,jj,kk] += dJx
                                Jy[ii,jj,kk] += dJy
                                Jz[ii,jj,kk] += dJz


    #print "    TOTAL=", np1, "/", np2
    return

#Yee shift current vector into staggered grid
def Yee_currents():

    Jp1 = np.zeros(3)
    J0 = np.zeros(3)

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                xmin,xmax, ymin,ymax, zmin,zmax = grid_limits(i,j,k)
                dx,dy,dz = grid_lengths(i,j,k)

                J0[0] = Jx[i,j,k]
                J0[1] = Jy[i,j,k]
                J0[2] = Jz[i,j,k]

                #Boundary  conditions and wrapping
                # TODO wrapping in every dimension done automatically here
                # correct this to check for Nx/y/z_wrap

                if oneD:
                    ii = i+1 if i < Nx-1 else 0
                    jj = j
                    kk = k
                elif twoD:
                    ii = i+1 if i < Nx-1 else 0
                    jj = j+1 if j < Ny-1 else 0
                    kk = k
                elif threeD:
                    ii = i+1 if i < Nx-1 else 0
                    jj = j+1 if j < Ny-1 else 0
                    kk = k+1 if k < Nz-1 else 0

                Jp1[0] = Jx[ii,jj,kk]                
                Jp1[1] = Jy[ii,jj,kk]                
                Jp1[2] = Jz[ii,jj,kk]                

                JYx[i,j,k] = (J0[0] + Jp1[0])/2.0
                JYy[i,j,k] = (J0[1] + Jp1[1])/2.0
                JYz[i,j,k] = (J0[2] + Jp1[2])/2.0


    return



#create similar small neighboring cubes as in c++ version
fieldsEx = np.zeros(27)
fieldsEy = np.zeros(27)
fieldsEz = np.zeros(27)

fieldsBx = np.zeros(27)
fieldsBy = np.zeros(27)
fieldsBz = np.zeros(27)

def EB_cube(i,j,k):

    ijk = 0
    for zdir in [-1,0,1]:
        kk = k + zdir 
        if kk < 0:
            kk += Nz
        if kk >= Nz:
            kk -= Nz

        for ydir in [-1, 0, 1]:
            jj = j + ydir 
            if jj < 0:
                jj += Ny
            if jj >= Ny:
                jj -= Ny

            for xdir in [-1, 0, 1]:
                ii = i + xdir 
                if ii < 0:
                    ii += Nx
                if ii >= Nx:
                    ii -= Nx

                if oneD:
                    fieldsEx[ijk] = Ex[ii,j,k]

                    fieldsBx[ijk] = Bx[ii,j,k]
                if twoD:
                    fieldsEx[ijk] = Ex[ii,jj,k]
                    fieldsEy[ijk] = Ey[ii,jj,k]

                    fieldsBx[ijk] = Bx[ii,jj,k]
                    fieldsBy[ijk] = By[ii,jj,k]
                if threeD:
                    fieldsEx[ijk] = Ex[ii,jj,kk]
                    fieldsEy[ijk] = Ey[ii,jj,kk]
                    fieldsEz[ijk] = Ez[ii,jj,kk]

                    fieldsBx[ijk] = Bx[ii,jj,kk]
                    fieldsBy[ijk] = By[ii,jj,kk]
                    fieldsBz[ijk] = Bz[ii,jj,kk]
                ijk += 1

    return

#wrapper functions for global fieldsE and fieldsB

#ijk gives the (Morton) z-ordering of von Neumann neighbors
def ijk(i,j,k):
    return (i+1) + (j+1)*3 + (k+1)*3*3

def exY(i,j,k):
    return fieldsEx[ijk(i,j,k)]
def eyY(i,j,k):
    return fieldsEy[ijk(i,j,k)]
def ezY(i,j,k):
    return fieldsEz[ijk(i,j,k)]

def bxY(i,j,k):
    return fieldsBx[ijk(i,j,k)]
def byY(i,j,k):
    return fieldsBy[ijk(i,j,k)]
def bzY(i,j,k):
    return fieldsBz[ijk(i,j,k)]


# First order staggered grid interpolation
def trilinear_staggered(xd,yd,zd):
    
    # from nodal points
    # f(i+dx) = f(i) + dx * (f(i+1)-f(i))
    # to staggered grid stored at midpoints
    # f at location i+dx  = half of f(i)+f(i-1) + dx*(f(i+1)-f(i-1))
    # where now f(i) means f at location i+1/2.
    # Then we apply the normal linear volume interpolation
    # Note that E and B differ in staggered grid locations

    ex = ( (1 - zd)*((1 - yd)*((0.5 - 0.5*xd)*exY(-1,0,0) + 0.5*exY(0,0,0) + 0.5*xd*exY(1,0,0)) + 
            yd*((0.5 - 0.5*xd)*exY(-1,1,0) + 0.5*exY(0,1,0) + 0.5*xd*exY(1,1,0))) + 
        zd*((1 - yd)*((0.5 - 0.5*xd)*exY(-1,0,1) + 0.5*exY(0,0,1) + 0.5*xd*exY(1,0,1)) + 
                yd*((0.5 - 0.5*xd)*exY(-1,1,1) + 0.5*exY(0,1,1) + 0.5*xd*exY(1,1,1))) )

    ey = ( (1 - zd)*((1 - yd)*(-0.5*(-1. + xd)*(eyY(0,-1,0) + eyY(0,0,0)) + 0.5*xd*(eyY(1,-1,0) + eyY(1,0,0))) + 
            yd*(-0.5*(-1. + xd)*(eyY(0,0,0) + eyY(0,1,0)) + 0.5*xd*(eyY(1,0,0) + eyY(1,1,0)))) + 
        zd*((1 - yd)*(-0.5*(-1. + xd)*(eyY(0,-1,1) + eyY(0,0,1)) + 0.5*xd*(eyY(1,-1,1) + eyY(1,0,1))) + 
                yd*(-0.5*(-1. + xd)*(eyY(0,0,1) + eyY(0,1,1)) + 0.5*xd*(eyY(1,0,1) + eyY(1,1,1)))) )

    ez = ( (1 - zd)*((1 - yd)*(-0.5*(-1. + xd)*(ezY(0,0,-1) + ezY(0,0,0)) + 0.5*xd*(ezY(1,0,-1) + ezY(1,0,0))) + 
            yd*(-0.5*(-1. + xd)*(ezY(0,1,-1) + ezY(0,1,0)) + 0.5*xd*(ezY(1,1,-1) + ezY(1,1,0)))) + 
        zd*((1 - yd)*(-0.5*(-1. + xd)*(ezY(0,0,0) + ezY(0,0,1)) + 0.5*xd*(ezY(1,0,0) + ezY(1,0,1))) + 
                yd*(-0.5*(-1. + xd)*(ezY(0,1,0) + ezY(0,1,1)) + 0.5*xd*(ezY(1,1,0) + ezY(1,1,1)))) )




    bx = ( (1 - zd)*((1 - yd)*(-0.25*(-1. + xd)*(bxY(0,-1,-1) + bxY(0,-1,0) + bxY(0,0,-1) + bxY(0,0,0)) + 
                0.25*xd*(bxY(1,-1,-1) + bxY(1,-1,0) + bxY(1,0,-1) + bxY(1,0,0))) + 
            yd*(-0.25*(-1. + xd)*(bxY(0,0,-1) + bxY(0,0,0) + bxY(0,1,-1) + bxY(0,1,0)) + 
                0.25*xd*(bxY(1,0,-1) + bxY(1,0,0) + bxY(1,1,-1) + bxY(1,1,0)))) + 
        zd*((1 - yd)*(-0.25*(-1. + xd)*(bxY(0,-1,0) + bxY(0,-1,1) + bxY(0,0,0) + bxY(0,0,1)) + 
                    0.25*xd*(bxY(1,-1,0) + bxY(1,-1,1) + bxY(1,0,0) + bxY(1,0,1))) + 
                yd*(-0.25*(-1. + xd)*(bxY(0,0,0) + bxY(0,0,1) + bxY(0,1,0) + bxY(0,1,1)) + 
                    0.25*xd*(bxY(1,0,0) + bxY(1,0,1) + bxY(1,1,0) + bxY(1,1,1)))) )

    by = ( (1 - zd)*((1 - yd)*(-0.25*(-1. + xd)*(byY(-1,0,-1) + byY(-1,0,0) + byY(0,0,-1) + byY(0,0,0)) + 
                0.25*xd*(byY(0,0,-1) + byY(0,0,0) + byY(1,0,-1) + byY(1,0,0))) + 
            yd*(-0.25*(-1. + xd)*(byY(-1,1,-1) + byY(-1,1,0) + byY(0,1,-1) + byY(0,1,0)) + 
                0.25*xd*(byY(0,1,-1) + byY(0,1,0) + byY(1,1,-1) + byY(1,1,0)))) + 
        zd*((1 - yd)*(-0.25*(-1. + xd)*(byY(-1,0,0) + byY(-1,0,1) + byY(0,0,0) + byY(0,0,1)) + 
                    0.25*xd*(byY(0,0,0) + byY(0,0,1) + byY(1,0,0) + byY(1,0,1))) + 
                yd*(-0.25*(-1. + xd)*(byY(-1,1,0) + byY(-1,1,1) + byY(0,1,0) + byY(0,1,1)) + 
                    0.25*xd*(byY(0,1,0) + byY(0,1,1) + byY(1,1,0) + byY(1,1,1)))) )

    bz = ( (1 - zd)*((1 - yd)*(-0.25*(-1. + xd)*(bzY(-1,-1,0) + bzY(-1,0,0) + bzY(0,-1,0) + bzY(0,0,0)) + 
                0.25*xd*(bzY(0,-1,0) + bzY(0,0,0) + bzY(1,-1,0) + bzY(1,0,0))) + 
            yd*(-0.25*(-1. + xd)*(bzY(-1,0,0) + bzY(-1,1,0) + bzY(0,0,0) + bzY(0,1,0)) + 
                0.25*xd*(bzY(0,0,0) + bzY(0,1,0) + bzY(1,0,0) + bzY(1,1,0)))) + 
        zd*((1 - yd)*(-0.25*(-1. + xd)*(bzY(-1,-1,1) + bzY(-1,0,1) + bzY(0,-1,1) + bzY(0,0,1)) + 
                    0.25*xd*(bzY(0,-1,1) + bzY(0,0,1) + bzY(1,-1,1) + bzY(1,0,1))) + 
                yd*(-0.25*(-1. + xd)*(bzY(-1,0,1) + bzY(-1,1,1) + bzY(0,0,1) + bzY(0,1,1)) + 
                    0.25*xd*(bzY(0,0,1) + bzY(0,1,1) + bzY(1,0,1) + bzY(1,1,1)))) )


    return ex, ey, ez, bx, by, bz


#Vay pusher and particle propagator
# note: we update every particle at once in vector format
def update_velocities(grid):

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                cell = grid[i,j,k]
                particles = cell.electrons

                xmin,xmax, ymin,ymax, zmin,zmax = grid_limits(i,j,k)
                dx,dy,dz = grid_lengths(i,j,k)

                q = 1.0
                m = me

                x = particles[:,0]
                y = particles[:,1]
                z = particles[:,2]
                ux = particles[:,3]
                uy = particles[:,4]
                uz = particles[:,5]

                xd = (x - xmin)/dx
                yd = (y - xmin)/dy
                zd = (z - xmin)/dz

                #interpolate E and B
                if zeroD:
                    Exi = Ex[i,j,k]
                    Eyi = Ey[i,j,k]
                    Ezi = Ez[i,j,k]
                    Bxi = Bx[i,j,k]
                    Byi = By[i,j,k]
                    Bzi = Bz[i,j,k]
                else:
                    EB_cube(i,j,k)
                    Exi, Eyi, Ezi, Bxi, Byi, Bzi = trilinear_staggered(xd,yd,zd)

                uxm = ux + q*e*Exi*dt/(2.0*m*c)
                uym = uy + q*e*Eyi*dt/(2.0*m*c)
                uzm = uz + q*e*Ezi*dt/(2.0*m*c)


                #Lorentz transform
                gamma = sqrt(1.0 + uxm*uxm + uym*uym + uzm*uzm)
                #gamma = 1.0

                #Calculate u'
                tx = q*e*Bxi*dt/(2.0*gamma*m*c)
                ty = q*e*Byi*dt/(2.0*gamma*m*c)
                tz = q*e*Bzi*dt/(2.0*gamma*m*c)

                ux0 = uxm + uym*tz - uzm*ty
                uy0 = uym + uzm*tx - uxm*tz
                uz0 = uzm + uxm*ty - uym*tx

                #calculate u+
                sx = 2.0*tx/(1.0 + tx*tx + ty*ty + tz*tz)
                sy = 2.0*ty/(1.0 + tx*tx + ty*ty + tz*tz)
                sz = 2.0*tz/(1.0 + tx*tx + ty*ty + tz*tz)

                uxp = uxm + uy0*sz - uz0*sy
                uyp = uym + uz0*sx - ux0*sz
                uzp = uzm + ux0*sy - uy0*sx

                # update velocities
                #t(dt/2) -> t(dt/2)
                particles[:,3] = uxp + q*e*Exi*dt/(2.0*m*c)
                particles[:,4] = uyp + q*e*Eyi*dt/(2.0*m*c)
                particles[:,5] = uzp + q*e*Ezi*dt/(2.0*m*c)
                
                #update locations and propagate particles
                uxn = particles[:,3]
                uyn = particles[:,4]
                uzn = particles[:,5]
                
                gamma = sqrt(1.0 + uxn*uxn + uyn*uyn + uzn*uzn)
                #gamma = 1.0

                if oneD:
                    particles[:,0] = particles[:,0] + (c*dt/gamma)*uxn
                if twoD:
                    particles[:,0] = particles[:,0] + (c*dt/gamma)*uxn
                    particles[:,1] = particles[:,1] + (c*dt/gamma)*uyn
                if threeD:
                    particles[:,0] = particles[:,0] + (c*dt/gamma)*uxn
                    particles[:,1] = particles[:,1] + (c*dt/gamma)*uyn
                    particles[:,2] = particles[:,2] + (c*dt/gamma)*uzn


    return


# sort particles between neighboring grid cells
def sort_particles_between_cells(grid):

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):

                xmin,xmax, ymin,ymax, zmin,zmax = grid_limits(i,j,k)
                dx,dy,dz = grid_lengths(i,j,k)

                ip = 0
                while (ip < grid[i,j,k].Npe):
                    particle = grid[i,j,k].electrons[ip,:]
                    iddf = (particle[0] - xmin - dx)/dx
                    jddf = (particle[1] - ymin - dy)/dy
                    kddf = (particle[2] - zmin - dz)/dz

                    idd = int(iddf) if iddf < 0 else int(iddf+1)
                    jdd = int(jddf) if jddf < 0 else int(jddf+1)
                    kdd = int(kddf) if kddf < 0 else int(kddf+1)

                    if idd == 0 and jdd == 0 and kdd == 0:
                        #print "inside"
                        ip += 1
                    else:
                        newi = i + idd
                        newj = j + jdd
                        newk = k + kdd

                        #periodic boundary conditions
                        remove_particle = False

                        if newi < 0:
                            if Nx_wrap:
                                newi += Nx
                                particle[0] += grid_xmax
                            else:
                                remove_particle = True
                        if newj < 0:
                            if Ny_wrap:
                                newj += Ny
                                particle[1] += grid_ymax
                            else:
                                remove_particle = True
                        if newk < 0:
                            if Nz_wrap:
                                newk += Nz
                                particle[2] += grid_zmax
                            else:
                                remove_particle = True

                        if newi >= Nx:
                            if Nx_wrap:
                                newi -= Nx
                                particle[0] -= grid_xmax
                            else:
                                remove_particle = True
                        if newj >= Ny:
                            if Ny_wrap:
                                newj -= Ny
                                particle[1] -= grid_ymax
                            else:
                                remove_particle = True
                        if newk >= Nz:
                            if Nz_wrap:
                                newk -= Nz
                                particle[2] -= grid_zmax
                            else:
                                remove_particle = True


                        #add to new cell
                        if (not remove_particle):
                            grid[newi, newj, newk].electrons = np.concatenate( (grid[newi,newj,newk].electrons, [particle] ), axis=0)
                            grid[newi, newj, newk].Npe += 1

                        #remove from previous cell
                        grid[i,j,k].electrons = np.delete(grid[i,j,k].electrons, ip, 0)
                        grid[i,j,k].Npe -= 1
                        ip += 1

    return 


def push_half_B():
    ds = np.zeros(3)
    EY = np.zeros(3)
    BY = np.zeros(3)
    EYp1 = np.zeros(3)

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):

                dx, dy, dz = grid_lengths(i,j,k)
                ds[0] = 1.0/dx
                ds[1] = 1.0/dy
                ds[2] = 1.0/dz

                EY[0] = Ex[i,j,k]                
                EY[1] = Ey[i,j,k]                
                EY[2] = Ez[i,j,k]                
                
                #Boundary  conditions and wrapping
                # TODO wrapping in every dimension done automatically here
                # correct this to check for Nx/y/z_wrap
                # EYp1[:] = 0.0

                if oneD:
                    ii = i+1 if i < Nx-1 else 0
                    jj = j
                    kk = k
                elif twoD:
                    ii = i+1 if i < Nx-1 else 0
                    jj = j+1 if j < Ny-1 else 0
                    kk = k
                elif threeD:
                    ii = i+1 if i < Nx-1 else 0
                    jj = j+1 if j < Ny-1 else 0
                    kk = k+1 if k < Nz-1 else 0

                EYp1[0] = Ex[ii,jj,kk]                
                EYp1[1] = Ey[ii,jj,kk]                
                EYp1[2] = Ez[ii,jj,kk]                

                BY = (c*dt/2.0) * np.cross(ds, EY - EYp1)

                #add to the field
                Bx[i,j,k] -= BY[0]
                By[i,j,k] -= BY[1]
                Bz[i,j,k] -= BY[2]


    return


def push_E():

    ds = np.zeros(3)
    JY = np.zeros(3)
    EY = np.zeros(3)
    BY = np.zeros(3)
    BYm1 = np.zeros(3)

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                dx, dy, dz = grid_lengths(i,j,k)
                ds[0] = 1.0/dx
                ds[1] = 1.0/dy
                ds[2] = 1.0/dz

                BY[0] = Bx[i,j,k]                
                BY[1] = By[i,j,k]                
                BY[2] = Bz[i,j,k]                
                
                #Boundary  conditions and wrapping
                # TODO wrapping in every dimension done automatically here
                # correct this to check for Nx/y/z_wrap
                # EYp1[:] = 0.0

                if oneD:
                    ii = i-1 if i > 0 else Nx-1
                    jj = j
                    kk = k
                elif twoD:
                    ii = i-1 if i < 0 else Nx-1
                    jj = j-1 if j < 0 else Ny-1
                    kk = k
                elif threeD:
                    ii = i-1 if i < 0 else Nx-1
                    jj = j-1 if j < 0 else Ny-1
                    kk = k-1 if k < 0 else Nz-1

                BYm1[0] = Bx[ii,jj,kk]                
                BYm1[1] = By[ii,jj,kk]                
                BYm1[2] = Bz[ii,jj,kk]                

                JY[0] = JYx[i,j,k]
                JY[1] = JYy[i,j,k]
                JY[2] = JYz[i,j,k]

                #E_n+1 = E_n + dt*[ curl B - 4pi J ]
                EY = (c*dt) * np.cross(ds, BY - BYm1) - 4.0*pi*dt*JY

                #add to the field
                Ex[i,j,k] += EY[0]
                Ey[i,j,k] += EY[1]
                Ez[i,j,k] += EY[2]


    return

##################################################

def collect_grid(grid):
    electrons = np.empty((0,6), dtype=float64)

    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                cell = grid[i,j,k]
                electrons = np.concatenate((electrons, cell.electrons), axis=0)
    return electrons




##################################################
##################################################
##################################################
def test_interp(grid):
    for k in range(Nz):
        for j in range(Ny):
            for i in range(Nx):
                cell = grid[i,j,k]

                xmin,xmax, ymin,ymax, zmin,zmax = grid_limits(i,j,k)
                dx,dy,dz = grid_lengths(i,j,k)

                print "grid limits"
                print xmin, xmax, dx
                print ymin, ymax, dy
                print zmin, zmax, dz

                #interpolate E and B
                EB_cube(i,j,k)

                y = ymin+dy
                z = zmin+dz
                for x in np.linspace(xmin, xmax, 10):
                    print "  x = ", x, "  |", y, z
                    xd = (x - xmin)/dx
                    yd = (y - xmin)/dy
                    zd = (z - xmin)/dz
                    print "  xd = ", xd,"  |", yd, zd

                    Exi, Eyi, Ezi, Bxi, Byi, Bzi = trilinear_staggered(xd,yd,zd)
                    print "   Ex=", Exi, "  |", Eyi, Ezi
                    print "   Bx=", Bxi, "  |", Byi, Bzi

    return
    


