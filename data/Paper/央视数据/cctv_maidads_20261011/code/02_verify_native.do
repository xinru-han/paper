version 17
clear all
set more off
do "/root/data/Paper/央视数据/cctv_maidads_20261011/ado/maidads_core.mata"
mata:
MD_K=7
MD_SCALE=J(1,7,1)
a=(.25,.15,.1,.1,.15,.1,.15)
b=(.1,.15,.2,.15,.1,.2,.1)
d=(1,2,1,.5,1,.7,2)
t=(2,1,2,1,3,1.5,1)
raw=(ln(a[1..6]:/a[7]),ln(b[1..6]:/b[7]),d,t,.6,3)
p=J(5,7,.)
for(i=1;i<=5;i++) for(j=1;j<=7;j++) p[i,j]=1+.05*j+.01*i
m=(100\150\230\400\650)
q=w=eta=om=oh=J(0,0,.)
u=J(0,1,.)
MD_predict(raw,1,p,m,q,w,u,eta,om,oh)
out=J(35,9,.)
cross=J(245,5,.)
for(i=1;i<=5;i++) {
    phi=(1-1/(1+exp(-u[i])))*a+1/(1+exp(-u[i]))*b
    gamma=(1-1/(1+exp(-.6*u[i])))*d+1/(1+exp(-.6*u[i]))*t
    Q=m[i]-sum(p[i,]:*gamma)
    for(j=1;j<=7;j++) {
        out[(i-1)*7+j,]=(i,j,p[i,j],m[i],u[i],q[i,j],eta[i,j],om[i,j],oh[i,j])
        for(l=1;l<=7;l++) {
            S=Q*phi[j]*phi[l]/(p[i,j]*p[i,l])-(j==l ? Q*phi[j]/p[i,j]^2 : 0)
            H=S*p[i,l]/q[i,j]
            M=H-eta[i,j]*w[i,l]
            cross[((i-1)*7+j-1)*7+l,]=(i,j,l,M,H)
        }
    }
}
MD_csv("/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/native_verification.csv","scenario,good,price,budget,utility,q,eta,marshallian_own,hicksian_own",out)
MD_csv("/root/data/Paper/央视数据/cctv_maidads_20261011/outputs/estimation/native_verification_prices.csv","scenario,good,price_good,marshallian,hicksian",cross)
end
